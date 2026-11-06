import argparse
import hashlib
import io
import json
import secrets
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from prometheus_client import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

METRICS = (
    "locals_login_operations_total",
    "locals_audio_uploads_total",
    "locals_playback_link_requests_total",
    "locals_review_submitted_total",
)

PROBE_CHECKS = Counter(
    "locals_probe_checks_total",
    "Completed scenario checks by result",
    labelnames=["scenario", "result"],
)



def main():
    for result in ("success", "failure"):
        PROBE_CHECKS.labels(scenario="login", result=result)
    p = argparse.ArgumentParser()
    p.add_argument("--api", default="http://localhost:18000")
    p.add_argument("--vm", default="http://localhost:8428")
    p.add_argument("--pace", type=float, default=0)
    p.add_argument("--result", type=Path)
    args = p.parse_args()
    tok = None
    def log(msg=""):
        print(msg, flush=True)
        if args.pace:
            time.sleep(args.pace)
    def check(cond, msg):
        if not cond:
            raise RuntimeError(msg)
    def req(path, method="GET", obj=None, data=None, ctype=None, timeout=30):
        hdrs = {}
        if tok:
            hdrs["Authorization"] = "Bearer " + tok
        if obj is not None:
            data = json.dumps(obj).encode()
            ctype = "application/json"
        if ctype:
            hdrs["Content-Type"] = ctype
        r = urllib.request.Request(args.api + path, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                body, code = resp.read(), resp.status
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}") from None
        log(f"{method} {path}: {code}")
        return code, json.loads(body) if body else None
    def probe_login(creds, expected_user_id, limit_seconds=6.0):
        nonlocal tok
        tok = None
        start_at = time.monotonic()
        deadline = start_at + limit_seconds
        remaining_seconds = limit_seconds
        login_result = {
        "success": False,
        "duration_seconds": None,
        "error": None,
        }
        try:
            code, auth = req("/api/v1/auth/login", "POST", creds, timeout=remaining_seconds)
            remaining_seconds = deadline - time.monotonic()
            check(remaining_seconds > 0, "Время проверки входа истекло")
            check(code == 200, "Вход: нужен 200")
            tok = auth["access_token"]
            check(isinstance(tok, str) and tok.strip()!="", "Неверный формат токена/ Пустой токен")
            code, me = req("/api/v1/me", timeout=remaining_seconds)
            remaining_seconds = deadline - time.monotonic()
            check(remaining_seconds > 0, "Время проверки входа истекло")
            check(code==200, "Проверка соответствия аккаунта не прошла: нужен 200")
            check(me["id"] == expected_user_id, "Не тот профиль")
        except Exception as exc:
            log(f"Вход и профиль: Ошибка {exc}")
            login_result["error"] = str(exc)
        else:
            log("Вход и профиль: ок")
            login_result["success"] = True
        finally:
            duration_sec = time.monotonic() - start_at
            login_result["duration_seconds"] = duration_sec
            log(f"Проверка login заняла {duration_sec:.3f} сек")
            log(json.dumps(login_result, ensure_ascii=False))
        return login_result
    def query(expr):
        qs = urllib.parse.urlencode({"query": expr, "nocache": "1"})
        with urllib.request.urlopen(args.vm + "/api/v1/query?" + qs, timeout=15) as resp:
            res = json.load(resp)
        check(res.get("status") == "success", "Ошибка запроса к VM")
        return res["data"]["result"]
    def ctrs():
        with urllib.request.urlopen(args.api + "/metrics", timeout=10) as resp:
            lines = resp.read().decode().splitlines()
        vals = {}
        for name in METRICS:
            hits = [s for s in lines if s.startswith(name + "{") and 'outcome="success"' in s]
            check(len(hits) == 1, f"Нет одного ряда success: {name}")
            vals[name] = float(hits[0].rsplit(" ", 1)[1])
        return vals

    dt = datetime.now(ZoneInfo("Asia/Yekaterinburg")).isoformat(timespec="seconds")
    log("Locals: проверка метрик")
    log(dt)
    for cmd in (
        ["kubectl", "-n", "monitoring", "get", "pods,svc", "-l", "app.kubernetes.io/instance=vmsingle"],
        ["kubectl", "-n", "locals", "get", "pods,svc"],
    ):
        log("$ " + " ".join(cmd))
        log(subprocess.check_output(cmd, text=True).rstrip())
    log("1. Сбор")
    tgts = query('up{job="locals-pods"}')
    check(any(r["metric"].get("pod", "").startswith("app-") for r in tgts), "Нет app в targets")
    check(any(r["metric"].get("pod") == "db-0" for r in tgts), "Нет db в targets")
    for r in tgts:
        check(float(r["value"][1]) == 1, "Таргет не up")
        log(f'up: {r["metric"]["pod"]} {r["metric"]["instance"]} = 1')
    pg = query('pg_up{job="locals-pods",pod="db-0"}')
    check(bool(pg) and all(float(r["value"][1]) == 1 for r in pg), "pg_up != 1")
    log('pg_up{pod="db-0"} = 1')
    pod = next(r["metric"]["pod"] for r in tgts if r["metric"].get("pod", "").startswith("app-"))
    sel = '{job="locals-pods",pod="' + pod + '"}'
    rt = ("python_info", "process_resident_memory_bytes", "monitoring_locals_http_requests_total")
    for name in rt:
        check(bool(query(name + sel)), "Нет метрики: " + name)
        log(name + ": есть в VM")
    prev = ctrs()
    log("2. Проверка API, тестовый акк")
    tag = secrets.token_hex(5)
    creds = {"email": f"metrics-{tag}@example.com", "password": secrets.token_urlsafe(24)}
    code, usr = req("/api/v1/auth/register", "POST", {**creds, "display_name": "Проверка метрик " + tag})
    check(code == 201, "Регистрация: нужен 201")
    login_result = probe_login(creds, usr["id"])
    if login_result["success"]:
        PROBE_CHECKS.labels(scenario="login", result="success").inc()
    else:
        PROBE_CHECKS.labels(scenario="login", result="failure").inc()
    check(login_result["success"], "Проверка входа не пройдена")
    _, art = req("/api/v1/artists", "POST", {"name": "Metrics demo " + tag})
    _, tr = req("/api/v1/tracks", "POST", {"title": "Metrics demo " + tag, "duration": 1, "artist_ids": [art["id"]]})
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 8000)
    raw = buf.getvalue()
    sha = hashlib.sha256(raw).hexdigest()
    sep = "LocalsMetrics" + secrets.token_hex(12)
    body = (f'--{sep}\r\nContent-Disposition: form-data; name="file"; filename="metrics-demo.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()
            + raw + f"\r\n--{sep}--\r\n".encode())
    code, media = req("/api/v1/media/audio", "POST", data=body, ctype="multipart/form-data; boundary=" + sep)
    check(code == 201 and media["sha256"] == sha, "Загрузка: не тот статус или хеш")
    _, meta = req(f'/api/v1/media/{media["id"]}')
    check(meta["sha256"] == sha, "Хеш в БД не совпал")
    log("WAV: загружен, хеш в БД совпал")
    req(f'/api/v1/tracks/{tr["id"]}/audio', "PUT", {"media_id": media["id"]})
    _, play = req(f'/api/v1/tracks/{tr["id"]}/playback')
    with urllib.request.urlopen(play["url"], timeout=20) as resp:
        raw2, code = resp.read(), resp.status
    check(code == 200 and hashlib.sha256(raw2).hexdigest() == sha, "Скачивание: не тот статус или хеш")
    log("Скачивание: 200, хеш совпал")
    req("/api/v1/ratings", "PUT", {"target_type": "track", "target_id": tr["id"], "value": 5})
    text = "Проверка метрик: рецензия создана и прочитана через API."
    code, rev = req("/api/v1/reviews", "POST", {"target_type": "track", "target_id": tr["id"], "text": text})
    check(code == 201, "Рецензия: нужен 201")
    _, got = req(f'/api/v1/reviews/{rev["id"]}')
    check(got["text"] == text, "Текст рецензии не совпал")
    log("Рецензия: создана, текст совпал")
    cur = ctrs()
    for name in METRICS:
        check(cur[name] >= prev[name] + 1, "Счётчик не вырос: " + name)
    log("3. Ждём счётчики в VM, scrape 15 сек")
    until = time.monotonic() + 100
    while True:
        vals = {}
        for name in METRICS:
            rows = query(name + '{job="locals-pods",pod="' + pod + '",outcome="success"}')
            if rows:
                vals[name] = float(rows[0]["value"][1])
        if all(vals.get(name, -1) >= cur[name] for name in METRICS):
            break
        check(time.monotonic() < until, "Счётчики не дошли до VM за 100 сек")
        time.sleep(3)
    for name in METRICS:
        log(f"{name}: {prev[name]:g} -> {vals[name]:g}")
    req("/api/v1/auth/logout", "POST")
    res = {"checked_at": dt, "status": "PASS", "targets": [r["metric"] for r in tgts],
           "pg_up": 1, "runtime_metrics": list(rt), "before": prev, "after": vals,
           "audio_sha256": sha, "audio_readback": "PASS", "review_readback": "PASS",
           "demo_ids": {"user": usr["id"], "artist": art["id"], "track": tr["id"], "media": media["id"], "review": rev["id"]}}
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    log("Всё ок: сбор, БД и 4 счётчика.")

if __name__ == "__main__":
    main()
