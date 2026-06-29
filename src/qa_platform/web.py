from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .literature import load_literature_markdown, render_markdown_document
from .orchestrator import OrchestratorAgent
from .storage import save_run


ROOT_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT_DIR / "static"


class QARequestHandler(BaseHTTPRequestHandler):
    orchestrator = OrchestratorAgent()

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._serve_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if self.path == "/literature":
            self._serve_literature_page()
            return
        if self.path == "/app.css":
            self._serve_file(STATIC_DIR / "app.css", "text/css; charset=utf-8")
            return
        if self.path == "/app.js":
            self._serve_file(STATIC_DIR / "app.js", "application/javascript; charset=utf-8")
            return
        self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path != "/api/process":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON payload"}, HTTPStatus.BAD_REQUEST)
            return

        title = (payload.get("title") or "Untitled demo").strip()
        requirements = (payload.get("requirements") or "").strip()
        if not requirements:
            self._send_json({"error": "Field 'requirements' is required."}, HTTPStatus.BAD_REQUEST)
            return

        result = self.orchestrator.process(title=title, requirements_text=requirements)
        response_payload = result.to_dict()
        saved_run = save_run(response_payload)
        response_payload["run_id"] = saved_run.run_id
        response_payload["stored_at"] = saved_run.stored_at
        response_payload["storage_path"] = saved_run.db_path
        self._send_json(response_payload, HTTPStatus.OK)

    def log_message(self, format: str, *args) -> None:
        return

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json({"error": "File not found"}, HTTPStatus.NOT_FOUND)
            return
        content = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict, status: HTTPStatus) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_literature_page(self) -> None:
        try:
            markdown_text = load_literature_markdown()
        except FileNotFoundError:
            self._send_json({"error": "Literature review not found"}, HTTPStatus.NOT_FOUND)
            return

        document = render_markdown_document(
            title="Litteraturstudie",
            eyebrow="Dokumentation",
            markdown_text=markdown_text,
        ).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(document)))
        self.end_headers()
        self.wfile.write(document)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), QARequestHandler)
    print(f"QA demo listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
