import json
import time
import urllib.error
import urllib.request

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
    r = urllib.request.Request(args.api + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            body, code = resp.read(), resp.status
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}") from None
    log(f"{method} {path}: {code}")
    return code, json.loads(body) if body else None