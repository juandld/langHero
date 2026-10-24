#!/usr/bin/env python3
"""Drive the running Chromium (CDP :9226) through actions on a URL.

Usage: cdp_act.py <url> <out_png> [commands...]

Each command is one of:
  wait <seconds>
  click <text-match>      (clicks the first visible <button> containing text)
  js <expression>         (runs JS in page context, prints eval result on stderr)
  shot <out_png>          (takes a mid-sequence screenshot, overrides final out)
  viewport <w> <h>

The sequence runs after navigation. A final screenshot is written to the main
<out_png> argument unless `shot` was used, in which case the LAST shot name wins.
"""
import base64
import json
import sys
import time

import websocket  # type: ignore


def _target():
    import urllib.request
    with urllib.request.urlopen("http://127.0.0.1:9226/json") as r:
        for t in json.loads(r.read()):
            if t.get("type") == "page":
                return t
    raise SystemExit("no page target")


class CDP:
    def __init__(self, ws):
        self.ws = websocket.create_connection(ws, timeout=25)
        self._id = 0

    def send(self, method, params=None):
        self._id += 1
        payload = {"id": self._id, "method": method}
        if params is not None:
            payload["params"] = params
        self.ws.send(json.dumps(payload))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def eval(self, expr):
        r = self.send(
            "Runtime.evaluate",
            {"expression": expr, "returnByValue": True, "awaitPromise": True},
        )
        res = r.get("result", {})
        if res.get("type") == "undefined":
            return None
        return res.get("value")

    def shot(self, out):
        s = self.send(
            "Page.captureScreenshot",
            {"format": "png", "captureBeyondViewport": False},
        )
        with open(out, "wb") as f:
            f.write(base64.b64decode(s["data"]))

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


CLICK_JS = r"""
(() => {
  const needle = %s;
  const nodes = document.querySelectorAll('button, [role=button], a');
  for (const n of nodes) {
    const t = (n.innerText || n.textContent || '').trim();
    if (t && t.toLowerCase().includes(needle.toLowerCase())) {
      const r = n.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {
        n.click();
        return `clicked: ${t.slice(0,80)}`;
      }
    }
  }
  return `no match for ${needle}`;
})()
"""


def main() -> int:
    url = sys.argv[1]
    out = sys.argv[2]
    cmds = sys.argv[3:]

    page = _target()
    cdp = CDP(page["webSocketDebuggerUrl"])
    try:
        cdp.send("Page.enable")
        cdp.send(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
        )
        cdp.send("Page.navigate", {"url": url})
        for _ in range(80):
            time.sleep(0.1)
            if cdp.eval("document.readyState") == "complete":
                break
        time.sleep(2)

        i = 0
        last_shot = out
        while i < len(cmds):
            c = cmds[i]
            if c == "wait":
                time.sleep(float(cmds[i + 1]))
                i += 2
            elif c == "click":
                r = cdp.eval(CLICK_JS % json.dumps(cmds[i + 1]))
                print(f"[click] {r}", file=sys.stderr)
                time.sleep(0.6)
                i += 2
            elif c == "js":
                r = cdp.eval(cmds[i + 1])
                print(f"[js] {r!r}", file=sys.stderr)
                i += 2
            elif c == "shot":
                cdp.shot(cmds[i + 1])
                last_shot = cmds[i + 1]
                print(cmds[i + 1])
                i += 2
            elif c == "viewport":
                cdp.send(
                    "Emulation.setDeviceMetricsOverride",
                    {
                        "width": int(cmds[i + 1]),
                        "height": int(cmds[i + 2]),
                        "deviceScaleFactor": 2,
                        "mobile": int(cmds[i + 1]) < 500,
                    },
                )
                i += 3
            else:
                raise SystemExit(f"unknown cmd: {c}")

        if last_shot == out:
            cdp.shot(out)
            print(out)
    finally:
        cdp.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
