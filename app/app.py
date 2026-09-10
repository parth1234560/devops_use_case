import json
import os
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "8080"))

LOG_FILE = os.getenv("LOG_FILE", "aws-ha-app.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

DB_USERNAME = os.getenv("DB_USERNAME", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "")


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":
            response = {
                "application": "aws-ha-app",
                "status": "running"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

            logging.info("GET /")

        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK\n")

            logging.info("GET /health")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found\n")

            logging.warning("404 %s", self.path)


if __name__ == "__main__":
    logging.info("Starting application on port %s", PORT)

    server = HTTPServer(("0.0.0.0", PORT), Handler)

    server.serve_forever()