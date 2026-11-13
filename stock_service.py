import json
import logging
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


STOCK = {"123": 15, "456": 80}
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:8001")
PRODUCT_REQUEST_TIMEOUT = 3


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class StockHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        match = re.fullmatch(r"/stock/([^/]+)", path)
        if match is None:
            send_json(self, 404, {"error": "Endpoint not found"})
            return

        product_id = match.group(1)
        self.log_message("Received stock lookup for productId=%s", product_id)
        product_url = f"{PRODUCT_SERVICE_URL.rstrip('/')}/products/{product_id}"
        self.log_message("Checking product service: GET %s", product_url)

        try:
            with urlopen(product_url, timeout=PRODUCT_REQUEST_TIMEOUT) as response:
                product = json.loads(response.read())
                if not isinstance(product, dict) or product.get("id") != int(product_id):
                    raise ValueError("Product Service returned an invalid product")
        except HTTPError as error:
            error.close()
            if error.code == 404:
                self.log_message("Product Service returned 404 for id=%s", product_id)
                send_json(self, 404, {"error": f"Product {product_id} not found"})
                return
            self.log_message("Product Service returned HTTP %s", error.code)
            send_json(self, 502, {"error": "Product Service returned an unexpected response"})
            return
        except (URLError, TimeoutError) as error:
            self.log_message("Product Service is unavailable: %s", error)
            send_json(self, 503, {"error": "Product Service is unavailable"})
            return
        except (json.JSONDecodeError, ValueError) as error:
            self.log_message("Product Service returned invalid data: %s", error)
            send_json(self, 502, {"error": "Product Service returned invalid data"})
            return

        quantity = STOCK.get(product_id, 0)
        self.log_message("Product id=%s exists; returning quantity=%s", product_id, quantity)
        send_json(self, 200, {"productId": int(product_id), "quantity": quantity})

    def log_message(self, format: str, *args: object) -> None:
        logging.info("Stock Service: " + format, *args)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    host = os.getenv("STOCK_HOST", "127.0.0.1")
    port = int(os.getenv("STOCK_PORT", "8002"))
    server = ThreadingHTTPServer((host, port), StockHandler)
    logging.info(
        "Stock Service listening on http://%s:%s (Product Service: %s)",
        host,
        port,
        PRODUCT_SERVICE_URL,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stock Service is shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
