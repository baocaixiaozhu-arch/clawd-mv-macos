#!/usr/bin/env python3
"""GitHub device-flow helper: start device auth, then poll in background.

Files (all under /tmp, token file is 0600):
  gh_dev.json   - device/user code + verification uri (readable)
  gh_token      - access token on success (0600, never printed)
  gh_status     - human readable status: pending / ok / error:<code>
"""
import json, os, sys, time, urllib.parse, urllib.request

CLIENT_ID = "178c6fc778ccc68e1d6a"          # public client id of the GitHub CLI (device flow)
SCOPE = "repo"
DEV = "/tmp/gh_dev.json"
TOKEN = "/tmp/gh_token"
STATUS = "/tmp/gh_status"


def post(url, data, accept="application/json"):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Accept": accept, "User-Agent": "clawd-mv-publisher"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def start():
    d = post("https://github.com/login/device/code", {"client_id": CLIENT_ID, "scope": SCOPE})
    json.dump(d, open(DEV, "w"))
    open(STATUS, "w").write("pending")
    return d


def poll():
    d = json.load(open(DEV))
    interval = int(d.get("interval", 5))
    deadline = time.time() + int(d.get("expires_in", 900))
    while time.time() < deadline:
        time.sleep(interval)
        try:
            r = post("https://github.com/login/oauth/access_token",
                     {"client_id": CLIENT_ID, "device_code": d["device_code"],
                      "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
        except Exception as e:                       # network hiccup: keep trying
            open(STATUS, "w").write(f"retry:{e.__class__.__name__}")
            continue
        if "access_token" in r:
            fd = os.open(TOKEN, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            os.write(fd, r["access_token"].encode())
            os.close(fd)
            open(STATUS, "w").write("ok")
            return 0
        err = r.get("error", "unknown")
        if err != "authorization_pending":
            if err == "slow_down":
                interval += 5
                open(STATUS, "w").write("pending")
                continue
            open(STATUS, "w").write(f"error:{err}")
            return 1
    open(STATUS, "w").write("error:expired")
    return 1


if __name__ == "__main__":
    if sys.argv[1] == "start":
        d = start()
        print(json.dumps({"user_code": d["user_code"], "uri": d["verification_uri"],
                          "expires_in": d["expires_in"]}, ensure_ascii=False))
    elif sys.argv[1] == "poll":
        sys.exit(poll())
    elif sys.argv[1] == "status":
        print(open(STATUS).read() if os.path.exists(STATUS) else "none")
