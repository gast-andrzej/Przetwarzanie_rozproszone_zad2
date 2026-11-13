import json
import logging
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


PRODUCTS = {
    "123": {"id": 123, "name": "Laptop", "price": 4500.00},
    "456": {"id": 456, "name": "Mysz", "price": 120.00},
}


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class ProductHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        match = re.fullmatch(r"/products/([^/]+)", path)
        if match is None:
            send_json(self, 404, {"error": "Endpoint not found"})
            return

        product_id = match.group(1)
        self.log_message("Received product lookup for id=%s", product_id)
        product = PRODUCTS.get(product_id)
        if product is None:
            self.log_message("Product id=%s was not found", product_id)
            send_json(self, 404, {"error": f"Product {product_id} not found"})
            return

        self.log_message("Returning product id=%s", product_id)
        send_json(self, 200, product)

    def log_message(self, format: str, *args: object) -> None:
        logging.info("Product Service: " + format, *args)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    host = os.getenv("PRODUCT_HOST", "127.0.0.1")
    port = int(os.getenv("PRODUCT_PORT", "8001"))
    server = ThreadingHTTPServer((host, port), ProductHandler)
    logging.info("Product Service listening on http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Product Service is shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
