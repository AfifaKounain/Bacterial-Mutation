"""Loopback-only JSON API for local BactoMut predictions."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from src.model_training import MODEL_DIRECTORY
from src.prediction import available_models, predict_mutation
from src.reference import REFERENCE_SEQUENCE

HOST = "127.0.0.1"
PORT = 8000
MAX_REQUEST_BYTES = 1_000_000


def _handler_for(model_directory: Path) -> type[BaseHTTPRequestHandler]:
    class BactoMutRequestHandler(BaseHTTPRequestHandler):
        server_version = "BactoMutLocalAPI/1.0"

        def do_GET(self) -> None:
            if self.path == "/health":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "service": "BactoMut local prediction API",
                        "available_models": available_models(model_directory),
                    },
                )
                return
            if self.path == "/models":
                self._send_json(
                    HTTPStatus.OK,
                    {"available_models": available_models(model_directory)},
                )
                return
            self._send_error_json(HTTPStatus.NOT_FOUND, "Endpoint not found.")

        def do_POST(self) -> None:
            if self.path != "/predict":
                self._send_error_json(HTTPStatus.NOT_FOUND, "Endpoint not found.")
                return
            raw_length = self.headers.get("Content-Length")
            try:
                body_length = int(raw_length) if raw_length is not None else -1
            except ValueError:
                self._send_error_json(HTTPStatus.BAD_REQUEST, "Invalid Content-Length.")
                return
            if body_length < 0:
                self._send_error_json(
                    HTTPStatus.LENGTH_REQUIRED,
                    "Provide a valid Content-Length header.",
                )
                return
            if body_length > MAX_REQUEST_BYTES:
                self._send_error_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    "Request body exceeds the 1 MB limit.",
                )
                return
            try:
                payload = json.loads(self.rfile.read(body_length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_error_json(
                    HTTPStatus.BAD_REQUEST,
                    "Request body must be valid UTF-8 JSON.",
                )
                return
            if not isinstance(payload, dict):
                self._send_error_json(
                    HTTPStatus.BAD_REQUEST,
                    "JSON body must be an object.",
                )
                return
            sequence = payload.get("sequence", REFERENCE_SEQUENCE)
            notation = payload.get("mutation")
            model_name = payload.get("model", "Random Forest")
            if not isinstance(sequence, str):
                self._send_error_json(
                    HTTPStatus.BAD_REQUEST,
                    "`sequence` must be a protein sequence string.",
                )
                return
            if notation is not None and not isinstance(notation, str):
                self._send_error_json(
                    HTTPStatus.BAD_REQUEST,
                    "`mutation` must be a string or null.",
                )
                return
            if not isinstance(model_name, str):
                self._send_error_json(
                    HTTPStatus.BAD_REQUEST,
                    "`model` must be a string.",
                )
                return
            if not available_models(model_directory):
                self._send_error_json(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    "No trained models are available. Run `python -m src.model_training` first.",
                )
                return
            try:
                result: dict[str, Any] = predict_mutation(
                    sequence=sequence,
                    notation=notation,
                    model_name=model_name,
                    model_directory=model_directory,
                )
            except FileNotFoundError as error:
                self._send_error_json(HTTPStatus.SERVICE_UNAVAILABLE, str(error))
                return
            except ValueError as error:
                self._send_error_json(HTTPStatus.UNPROCESSABLE_ENTITY, str(error))
                return
            self._send_json(HTTPStatus.OK, result)

        def _send_error_json(self, status: HTTPStatus, message: str) -> None:
            self._send_json(status, {"error": message})

        def _send_json(self, status: HTTPStatus, body: dict[str, Any]) -> None:
            encoded = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format_string: str, *args: object) -> None:
            super().log_message(format_string, *args)

    return BactoMutRequestHandler


def create_server(
    port: int = PORT,
    model_directory: Path = MODEL_DIRECTORY,
) -> ThreadingHTTPServer:
    """Create an API server bound only to localhost."""
    return ThreadingHTTPServer(
        (HOST, port),
        _handler_for(model_directory),
    )


def main() -> None:
    server = create_server()
    print(f"BactoMut API listening at http://{HOST}:{server.server_port}")
    print("Endpoints: GET /health, GET /models, POST /predict")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping BactoMut API.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
