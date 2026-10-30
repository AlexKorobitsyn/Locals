import json
import time
import urllib.error
import urllib.request
import getpass

def check(cond, msg):
    if not cond:
        raise RuntimeError(msg)

def log(msg=""):
    print(msg, flush=True)

def req(base_url, path, method="GET", obj=None, data=None, ctype=None, timeout=30, token=None,):
    hdrs = {}
    if token:
        hdrs["Authorization"] = "Bearer " + token
    if obj is not None:
        data = json.dumps(obj).encode()
        ctype = "application/json"
    if ctype:
        hdrs["Content-Type"] = ctype
    r = urllib.request.Request(base_url + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            body, code = resp.read(), resp.status
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}") from None
    log(f"{method} {path}: {code}")
    return code, json.loads(body) if body else None

def probe_login(creds, expected_user_id, limit_seconds=6.0):
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
        code, auth = req("http://localhost:8080", "/api/v1/auth/login", "POST", creds,  timeout=remaining_seconds)
        remaining_seconds = deadline - time.monotonic()
        check(remaining_seconds > 0, "Время проверки входа истекло")
        check(code == 200, "Вход: нужен 200")
        tok = auth["access_token"]
        check(isinstance(tok, str) and tok.strip()!="", "Неверный формат токена/ Пустой токен")
        code, me = req("http://localhost:8080", "/api/v1/me",  token=tok, timeout=remaining_seconds)
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

def main():
    email = input("Почта: ").strip()
    password = getpass.getpass("Пароль: ")
    excepted_user_id = int(input("ID тестового пользователя: "))
    creds = {"email": email, "password": password}
    login_result = probe_login(creds=creds, expected_user_id=excepted_user_id)


if __name__ == "__main__":
    main()