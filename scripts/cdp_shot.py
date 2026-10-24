#!/usr/bin/env python3
"""Drive the running Chromium (CDP :9226) to screenshot a URL at a given viewport.

Usage: cdp_shot.py <url> <out_png> [width=390] [height=844]

Writes a PNG to <out_png> and prints the saved path.
"""
import base64
import json
import sys
import time

import websocket  # type: ignore

CDP_HOST = "127.0.0.1"
CDP_PORT = 9226


def _tabs():
    import urllib.request
    with urllib.request.urlopen(f"http://{CDP_HOST}:{CDP_PORT}/json") as r:
        return json.loads(r.read().decode())


def _page_target():
    for t in _tabs():
        if t.get("type") == "page":
            return t
    raise SystemExit("No page target found in Chromium")


class CDP:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=20)
        self._msg_id = 0

    def send(self, method: str, params: dict | None = None):
        self._msg_id += 1
        payload = {"id": self._msg_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.ws.send(json.dumps(payload))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self._msg_id:
                if "error" in msg:
                    raise RuntimeError(f"{method} failed: {msg['error']}")
                return msg.get("result", {})

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def main() -> int:
    url = sys.argv[1]
    out_png = sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 390
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 844

    page = _page_target()
    cdp = CDP(page["webSocketDebuggerUrl"])
    try:
        # Phone-like viewport (iPhone 14 Pro default) with device pixel ratio 2
        cdp.send(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height,
                "deviceScaleFactor": 2,
                "mobile": width < 500,
            },
        )
        cdp.send("Page.enable")
        cdp.send("Page.navigate", {"url": url})
        # Wait up to ~8 s for the page to be visibly settled
        for _ in range(80):
            time.sleep(0.1)
            state = cdp.send(
                "Runtime.evaluate",
                {"expression": "document.readyState"},
            )
            if state.get("result", {}).get("value") == "complete":
                break
        time.sleep(2)  # give Svelte a moment to hydrate / state machine to advance
        shot = cdp.send(
            "Page.captureScreenshot",
            {"format": "png", "captureBeyondViewport": False},
        )
        png = base64.b64decode(shot["data"])
        with open(out_png, "wb") as f:
            f.write(png)
        print(out_png)
    finally:
        cdp.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
