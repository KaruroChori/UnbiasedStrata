#!/usr/bin/env python3
"""One chat request with a picture to an OpenAI-style server: ask-image.py <url> <png> <question> [out.json]"""
import base64, json, sys, time, urllib.request
url, png, q = sys.argv[1], sys.argv[2], sys.argv[3]
out = sys.argv[4] if len(sys.argv) > 4 else None
b64 = base64.b64encode(open(png, 'rb').read()).decode()
body = {"model": "x", "temperature": 0, "max_tokens": 400, "chat_template_kwargs": {"enable_thinking": False},
        "messages": [{"role": "user", "content": [{"type": "text", "text": q},
                                                  {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}]}]}
t0 = time.time()
req = urllib.request.Request(url.rstrip('/') + "/v1/chat/completions", data=json.dumps(body).encode(), headers={"content-type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.loads(r.read()); d["_wall_s"] = round(time.time() - t0, 1)
except urllib.error.HTTPError as e:
    d = {"http_error": e.code, "body": e.read().decode(errors="replace")[:2000], "_wall_s": round(time.time() - t0, 1)}
if out: json.dump(d, open(out, 'w'), indent=1)
if "choices" in d:
    print(d["choices"][0]["message"]["content"]); print("--", json.dumps({"usage": d.get("usage"), "timings": d.get("timings"), "wall_s": d["_wall_s"]}))
else:
    print(json.dumps(d, indent=1)[:2000])
