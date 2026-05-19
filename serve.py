"""
Production-like server: serves the SvelteKit static build and proxies /api/* to the backend.
Single port, single tunnel — no CORS issues.
"""
import http.server
import urllib.request
import os
import sys

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "build")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8100")
PORT = int(os.environ.get("PORT", "5200"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_request(self, method):
        # Proxy /api/*, /stream/*, /examples/*, /narrative/* to backend
        if self.path.startswith(("/api/", "/stream/", "/examples/", "/narrative/", "/openapi.json")):
            url = BACKEND_URL + self.path
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            headers = {}
            for key in ("Content-Type", "Authorization", "Accept"):
                val = self.headers.get(key)
                if val:
                    headers[key] = val

            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    self.send_response(resp.status)
                    for key, val in resp.getheaders():
                        if key.lower() not in ("transfer-encoding", "connection"):
                            self.send_header(key, val)
                    self.end_headers()
                    self.wfile.write(resp.read())
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self.send_response(502)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Backend error: {e}".encode())
            return

        # SvelteKit SPA fallback: if file doesn't exist, serve index.html
        if method == "GET":
            file_path = os.path.join(FRONTEND_DIR, self.path.lstrip("/"))
            if not os.path.isfile(file_path) and not self.path.startswith("/_app/"):
                self.path = "/index.html"
            super().do_GET()

    def do_GET(self):
        self.do_request("GET")

    def do_POST(self):
        self.do_request("POST")

    def do_PUT(self):
        self.do_request("PUT")

    def do_DELETE(self):
        self.do_request("DELETE")

    def log_message(self, format, *args):
        # Quieter logging
        pass


if __name__ == "__main__":
    print(f"Serving frontend from {FRONTEND_DIR}")
    print(f"Proxying /api/* to {BACKEND_URL}")
    print(f"Listening on http://0.0.0.0:{PORT}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
