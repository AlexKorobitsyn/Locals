import argparse
import hashlib
import http.client
import io
import json
import math
import os
import secrets
import signal
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

from prometheus_client import CollectorRegistry, Counter, Gauge, start_http_server

SCENARIOS = ("login", "audio_upload", "review")
PROBE_ERRORS = (RuntimeError, OSError, ValueError, KeyError, TypeError, http.client.HTTPException)

def check(condition, message):
    if not condition:
        raise RuntimeError(message)

def log(**fields):
    print(json.dumps(fields, ensure_ascii=False), flush=True)

def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as file:
        json.dump(value, file, ensure_ascii=False)
    os.replace(temporary, path)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None

class Client:
    def __init__(self, base_url, storage_url=None):
        self.base_url = base_url.rstrip("/")
        self.storage_url = storage_url
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, path, method="GET", obj=None, data=None, ctype=None, token=None, timeout=6):
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        if obj is not None:
            data, ctype = json.dumps(obj).encode(), "application/json"
        if ctype:
            headers["Content-Type"] = ctype
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=timeout) as response:
                body = response.read()
                return response.status, json.loads(body) if body else None
        except urllib.error.HTTPError as error:
            if error.code == 307:
                return error.code, {"url": error.headers["Location"]}
            raise RuntimeError(f"{method} {path}: HTTP {error.code}") from None

    def download(self, url, timeout):
        source = urllib.parse.urlsplit(url)
        check(source.scheme in ("http", "https") and source.netloc, "Некорректная ссылка на аудио")
        headers = {}
        if self.storage_url:
            destination = urllib.parse.urlsplit(self.storage_url)
            url = urllib.parse.urlunsplit((destination.scheme, destination.netloc, source.path, source.query, ""))
            headers["Host"] = source.netloc
        request = urllib.request.Request(url, headers=headers)
        try:
            with self.opener.open(request, timeout=timeout) as response:
                check(response.status == 200, "Скачивание: нужен 200")
                return response.read(16045)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Скачивание аудио: HTTP {error.code}") from None
        except urllib.error.URLError:
            raise RuntimeError("Хранилище аудио недоступно") from None

def prepare(client, path):
    state = json.loads(path.read_text()) if path.exists() else {}
    if not state:
        credentials = {"email": f"slo-{secrets.token_hex(6)}@example.com", "password": secrets.token_urlsafe(24)}
        code, user = client.request("/api/v1/auth/register", "POST", {**credentials, "display_name": "SLO prober"})
        check(code == 201, "Регистрация: нужен 201")
        state = {"credentials": credentials, "user_id": user["id"]}
        save_json(path, state)
    code, auth = client.request("/api/v1/auth/login", "POST", state["credentials"])
    check(code == 200, "Вход: нужен 200")
    token = auth["access_token"]
    try:
        if "artist_id" not in state:
            code, artist = client.request("/api/v1/artists", "POST", {"name": "SLO prober"}, token=token)
            check(code == 201, "Артист: нужен 201")
            state["artist_id"] = artist["id"]
            save_json(path, state)
        if "track_id" not in state:
            code, track = client.request("/api/v1/tracks", "POST", {"title": "SLO probe", "duration": 1, "artist_ids": [state["artist_id"]]}, token=token)
            check(code == 201, "Трек: нужен 201")
            state["track_id"] = track["id"]
            save_json(path, state)
        code, _ = client.request("/api/v1/ratings", "PUT", {"target_type": "track", "target_id": state["track_id"], "value": 5}, token=token)
        check(code == 200, "Оценка: нужен 200")
    finally:
        client.request("/api/v1/auth/logout", "POST", token=token)
    log(event="prepared", user_id=state["user_id"], track_id=state["track_id"], state=str(path))

class Prober:
    def __init__(self, client, state, pending_path, interval=15, limits=(6, 12, 6)):
        self.client, self.state = client, state
        self.pending_path, self.interval = Path(pending_path), interval
        self.limits = dict(zip(SCENARIOS, limits))
        self.pending = json.loads(self.pending_path.read_text()) if self.pending_path.exists() else {"sessions": [], "media": [], "reviews": []}
        self.registry = CollectorRegistry()
        self.checks = Counter("locals_probe_checks_total", "Completed scenario checks", ["scenario", "result"], registry=self.registry)
        self.duration = Gauge("locals_probe_duration_seconds", "Last scenario duration without cleanup", ["scenario"], registry=self.registry)
        self.completed = Gauge("locals_probe_last_completed_timestamp_seconds", "Last completed check", ["scenario"], registry=self.registry)
        self.success = Gauge("locals_probe_success", "Last check result", ["scenario"], registry=self.registry)
        self.cleanup_errors = Counter("locals_probe_cleanup_errors_total", "Failed cleanup attempts", registry=self.registry)
        self.backlog = Gauge("locals_probe_cleanup_pending", "Resources awaiting cleanup", registry=self.registry)
        self.period = Gauge("locals_probe_interval_seconds", "Target interval per scenario", registry=self.registry)
        self.period.set(interval)
        limit = Gauge("locals_probe_limit_seconds", "Good check duration limit", ["scenario"], registry=self.registry)
        slo = Gauge("locals_probe_slo_ratio", "SLO over rolling 30 days", ["scenario"], registry=self.registry)
        sla = Gauge("locals_probe_sla_ratio", "SLA over rolling 30 days", ["scenario"], registry=self.registry)
        for scenario in SCENARIOS:
            for result in ("success", "failure"):
                self.checks.labels(scenario=scenario, result=result)
            self.completed.labels(scenario=scenario).set(0)
            self.success.labels(scenario=scenario).set(0)
            self.duration.labels(scenario=scenario).set(0)
            limit.labels(scenario=scenario).set(self.limits[scenario])
            slo.labels(scenario=scenario).set(0.995)
            sla.labels(scenario=scenario).set(0.99)
        self.persist()

    def persist(self):
        save_json(self.pending_path, self.pending)
        self.backlog.set(sum(len(items) for items in self.pending.values()))

    def login(self, timeout):
        code, auth = self.client.request("/api/v1/auth/login", "POST", self.state["credentials"], timeout=timeout)
        check(code == 200, "Вход: нужен 200")
        token = auth["access_token"]
        check(isinstance(token, str) and token.strip(), "Неверный или пустой токен")
        self.pending["sessions"].append(token)
        self.persist()
        return token

    def probe_login(self, deadline, limit):
        remaining_seconds = limit
        token = self.login(remaining_seconds)
        remaining_seconds = deadline - time.monotonic()
        check(remaining_seconds > 0, "Время проверки входа истекло")
        code, user = self.client.request("/api/v1/me", token=token, timeout=remaining_seconds)
        remaining_seconds = deadline - time.monotonic()
        check(remaining_seconds > 0, "Время проверки входа истекло")
        check(code == 200 and user["id"] == self.state["user_id"], "Неверный профиль")

    def probe_audio_upload(self, deadline, limit):
        token = self.login(limit)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(secrets.token_bytes(16000))
        raw = buffer.getvalue()
        digest = hashlib.sha256(raw).hexdigest()
        boundary = "LocalsProbe" + secrets.token_hex(12)
        body = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="slo-probe.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode() + raw + f"\r\n--{boundary}--\r\n".encode()
        code, media = self.client.request("/api/v1/media/audio", "POST", data=body, ctype="multipart/form-data; boundary=" + boundary, token=token, timeout=limit)
        if isinstance(media, dict) and isinstance(media.get("id"), int):
            self.pending["media"].append(media["id"])
            self.persist()
        check(code == 201 and media["sha256"] == digest, "Загрузка: неверный статус или SHA-256")
        code, metadata = self.client.request(f'/api/v1/media/{media["id"]}', token=token, timeout=limit)
        check(code == 200 and metadata["sha256"] == digest, "Неверные метаданные аудио")
        code, location = self.client.request(f'/api/v1/media/{media["id"]}/content', token=token, timeout=limit)
        check(code == 307, "Нет ссылки на сохранённое аудио")
        received = self.client.download(location["url"], timeout=limit)
        check(hashlib.sha256(received).hexdigest() == digest, "Содержимое аудио не совпало")

    def probe_review(self, deadline, limit):
        token = self.login(limit)
        query = urllib.parse.urlencode({"target_type": "track", "target_id": self.state["track_id"], "limit": 100})
        code, existing = self.client.request("/api/v1/reviews?" + query, token=token, timeout=limit)
        check(code == 200, "Не удалось проверить старую тестовую рецензию")
        for review in existing["items"]:
            if review["author"]["id"] == self.state["user_id"]:
                self.client.request(f'/api/v1/reviews/{review["id"]}', "DELETE", token=token, timeout=limit)
        text = "Проверка SLO: " + secrets.token_hex(12)
        payload = {"target_type": "track", "target_id": self.state["track_id"], "text": text}
        code, review = self.client.request("/api/v1/reviews", "POST", payload, token=token, timeout=limit)
        if isinstance(review, dict) and isinstance(review.get("id"), int):
            self.pending["reviews"].append(review["id"])
            self.persist()
        check(code == 201, "Создание рецензии: нужен 201")
        code, received = self.client.request(f'/api/v1/reviews/{review["id"]}', token=token, timeout=limit)
        check(code == 200 and received["text"] == text, "Текст рецензии не совпал")
        check(received["target_id"] == self.state["track_id"] and received["author"]["id"] == self.state["user_id"], "Неверный автор или трек рецензии")

    def cleanup(self):
        deadline = time.monotonic() + 10
        token = self.pending["sessions"][-1] if self.pending["sessions"] else None
        for kind, route in (("reviews", "/api/v1/reviews/"), ("media", "/api/v1/media/"), ("sessions", "/api/v1/auth/logout")):
            for item in self.pending[kind][:10]:
                if time.monotonic() >= deadline:
                    self.persist()
                    return
                try:
                    if kind == "sessions":
                        self.client.request(route, "POST", token=item, timeout=2)
                    else:
                        check(token is not None, "Нет сессии для удаления тестовых данных")
                        self.client.request(route + str(item), "DELETE", token=token, timeout=2)
                except PROBE_ERRORS as error:
                    missing = f"HTTP {401 if kind == 'sessions' else 404}" in str(error)
                    if not missing:
                        self.cleanup_errors.inc()
                        log(event="cleanup_failed", resource=kind, error=str(error))
                        continue
                self.pending[kind].remove(item)
                self.persist()

    def run_check(self, scenario):
        start_at = time.monotonic()
        limit = self.limits[scenario]
        result = {"scenario": scenario, "success": False, "error": None}
        try:
            getattr(self, "probe_" + scenario)(start_at + limit, limit)
            check(time.monotonic() - start_at <= limit, "Превышено допустимое время сценария")
        except PROBE_ERRORS as error:
            result["error"] = str(error)
        else:
            result["success"] = True
        result["duration_seconds"] = time.monotonic() - start_at
        self.checks.labels(scenario=scenario, result="success" if result["success"] else "failure").inc()
        self.duration.labels(scenario=scenario).set(result["duration_seconds"])
        self.success.labels(scenario=scenario).set(int(result["success"]))
        self.completed.labels(scenario=scenario).set(time.time())
        log(**result)
        self.cleanup()
        return result

    def run(self, stop, once=False):
        while not stop.is_set():
            start_at = time.monotonic()
            for scenario in SCENARIOS:
                if stop.is_set():
                    break
                self.run_check(scenario)
            if once:
                break
            stop.wait(max(0, self.interval - (time.monotonic() - start_at)))

def positive_number(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Нужно конечное положительное число")
    return number

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=os.getenv("PROBE_API_URL", "http://localhost:8080"))
    parser.add_argument("--storage-url", default=os.getenv("PROBE_STORAGE_URL"))
    parser.add_argument("--state", type=Path, default=Path("data/prober.json"))
    parser.add_argument("--pending", type=Path, default=Path("data/prober-pending.json"))
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=positive_number, default=15)
    parser.add_argument("--login-limit", type=positive_number, default=6)
    parser.add_argument("--audio-limit", type=positive_number, default=12)
    parser.add_argument("--review-limit", type=positive_number, default=6)
    parser.add_argument("--listen", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9105)
    args = parser.parse_args()
    client = Client(args.api, args.storage_url)
    if args.prepare:
        prepare(client, args.state)
        return
    check(args.state.exists(), "Сначала запустите --prepare")
    state = json.loads(args.state.read_text())
    check(all(name in state for name in ("credentials", "user_id", "track_id")), "Не завершена подготовка: запустите --prepare")
    prober = Prober(client, state, args.pending, args.interval, (args.login_limit, args.audio_limit, args.review_limit))
    server, thread = start_http_server(args.port, addr=args.listen, registry=prober.registry)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    try:
        prober.run(stop, args.once)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()

if __name__ == "__main__":
    main()
