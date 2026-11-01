import hashlib
import importlib.util
import json
import tempfile
import threading
import time
import unittest
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from prometheus_client import start_http_server

spec = importlib.util.spec_from_file_location("prober", Path(__file__).with_name("prober.py"))
prober = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prober)

class ProberTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.mode = "healthy"
        self.objects = {}
        self.reviews = {}
        self.sessions = set()
        self.download_headers = []
        self.delay = 0
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def handle_request(self):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                obj = json.loads(raw) if raw and self.headers.get("Content-Type") == "application/json" else {}
                path = self.path.split("?")[0]
                code, result = 200, None
                if owner.mode == "outage":
                    code = 503
                elif path == "/api/v1/auth/login":
                    if owner.mode == "rejected":
                        code = 401
                    else:
                        token = f"token-{time.monotonic_ns()}"
                        owner.sessions.add(token)
                        result = {"access_token": "" if owner.mode == "bad_token" else token}
                elif path == "/api/v1/me":
                    time.sleep(owner.delay)
                    result = {"id": 999 if owner.mode == "wrong_user" else 1}
                elif path == "/api/v1/auth/logout":
                    owner.sessions.discard(self.headers.get("Authorization", "").removeprefix("Bearer "))
                    code = 204
                elif path == "/api/v1/media/audio":
                    message = BytesParser(policy=default).parsebytes(b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + raw)
                    body = next(message.iter_parts()).get_payload(decode=True)
                    owner.objects[10] = body
                    code, result = 201, {"id": 10, "sha256": hashlib.sha256(body).hexdigest()}
                elif path == "/api/v1/media/10/content":
                    self.send_response(307)
                    self.send_header("Location", "http://localhost:9000/object/10?signature=keep")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                elif path == "/object/10":
                    owner.download_headers.append(dict(self.headers))
                    body = b"corrupt" if owner.mode == "corrupt_audio" else owner.objects[10]
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                elif path == "/api/v1/media/10":
                    if self.command == "DELETE":
                        if owner.mode == "cleanup_failure":
                            code = 503
                        else:
                            owner.objects.pop(10, None)
                            code = 204
                    else:
                        result = {"sha256": hashlib.sha256(owner.objects[10]).hexdigest()}
                elif path == "/api/v1/reviews":
                    if self.command == "GET":
                        result = {"items": list(owner.reviews.values())}
                    else:
                        result = {"id": 20, **obj, "author": {"id": 1}}
                        owner.reviews[20] = result
                        code = 201
                elif path == "/api/v1/reviews/20":
                    if self.command == "DELETE":
                        owner.reviews.pop(20, None)
                        code = 204
                    else:
                        result = dict(owner.reviews[20])
                        if owner.mode == "wrong_review":
                            result["text"] = "wrong"
                else:
                    code = 404
                body = json.dumps(result).encode() if result is not None else b""
                self.send_response(code)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except BrokenPipeError:
                    pass
            do_GET = handle_request
            do_POST = handle_request
            do_DELETE = handle_request
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        url = f"http://127.0.0.1:{self.server.server_port}"
        self.client = prober.Client(url, url)
        self.pending = Path(self.temporary.name) / "pending.json"
        self.probe = prober.Prober(self.client, {"credentials": {"email": "probe@example.com", "password": "secret"}, "user_id": 1, "track_id": 2}, self.pending)
    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.temporary.cleanup()
    def test_three_scenarios_readback_cleanup_and_metrics(self):
        for scenario in prober.SCENARIOS:
            self.assertTrue(self.probe.run_check(scenario)["success"])
            self.assertEqual(self.probe.registry.get_sample_value("locals_probe_checks_total", {"scenario": scenario, "result": "success"}), 1)
            self.assertEqual(self.probe.registry.get_sample_value("locals_probe_checks_total", {"scenario": scenario, "result": "failure"}), 0)
        self.assertFalse(self.objects or self.reviews or self.sessions)
        self.assertEqual(self.download_headers[0]["Host"], "localhost:9000")
        self.assertNotIn("Authorization", self.download_headers[0])
    def test_outage_counts_each_failure_and_recovery_continues(self):
        self.mode = "outage"
        self.probe.run(threading.Event(), once=True)
        self.mode = "healthy"
        self.probe.run(threading.Event(), once=True)
        for scenario in prober.SCENARIOS:
            for result in ("success", "failure"):
                self.assertEqual(self.probe.registry.get_sample_value("locals_probe_checks_total", {"scenario": scenario, "result": result}), 1)
    def test_incorrect_results_are_failures(self):
        for mode, scenario in (("wrong_user", "login"), ("bad_token", "login"), ("rejected", "login"), ("corrupt_audio", "audio_upload"), ("wrong_review", "review")):
            self.mode = mode
            self.assertFalse(self.probe.run_check(scenario)["success"], mode)
    def test_slow_profile_is_failure(self):
        self.delay = 0.03
        self.probe.limits["login"] = 0.02
        self.assertFalse(self.probe.run_check("login")["success"])
    def test_cleanup_backlog_survives_restart(self):
        self.mode = "cleanup_failure"
        self.assertTrue(self.probe.run_check("audio_upload")["success"])
        self.assertEqual(json.loads(self.pending.read_text())["media"], [10])
        restored = prober.Prober(self.client, self.probe.state, self.pending)
        self.mode = "healthy"
        restored.run_check("login")
        self.assertFalse(self.objects)
        self.assertEqual(json.loads(self.pending.read_text()), {"sessions": [], "media": [], "reviews": []})
    def test_metrics_endpoint_remains_up_during_application_outage(self):
        server, thread = start_http_server(0, addr="127.0.0.1", registry=self.probe.registry)
        try:
            self.mode = "outage"
            self.probe.run(threading.Event(), once=True)
            with prober.urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/metrics") as response:
                body = response.read().decode()
            self.assertIn('locals_probe_checks_total{result="failure",scenario="audio_upload"} 1.0', body)
            self.assertIn("locals_probe_last_completed_timestamp_seconds", body)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

if __name__ == "__main__":
    unittest.main()
