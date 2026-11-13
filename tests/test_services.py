import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

import stock_service
from product_service import ProductHandler
from stock_service import StockHandler


class ServiceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.product_server = ThreadingHTTPServer(("127.0.0.1", 0), ProductHandler)
        cls.product_thread = threading.Thread(
            target=cls.product_server.serve_forever, daemon=True
        )
        cls.product_thread.start()

        product_host, product_port = cls.product_server.server_address
        stock_service.PRODUCT_SERVICE_URL = f"http://{product_host}:{product_port}"
        cls.stock_server = ThreadingHTTPServer(("127.0.0.1", 0), StockHandler)
        cls.stock_thread = threading.Thread(
            target=cls.stock_server.serve_forever, daemon=True
        )
        cls.stock_thread.start()
        stock_host, stock_port = cls.stock_server.server_address
        cls.stock_url = f"http://{stock_host}:{stock_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.stock_server.shutdown()
        cls.product_server.shutdown()
        cls.stock_server.server_close()
        cls.product_server.server_close()
        cls.stock_thread.join()
        cls.product_thread.join()

    def get_json(self, path: str) -> tuple[int, dict]:
        with urlopen(f"{self.stock_url}{path}") as response:
            return response.status, json.loads(response.read())

    def test_existing_product_returns_stock(self) -> None:
        status, payload = self.get_json("/stock/123")

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"productId": 123, "quantity": 15})

    def test_missing_product_returns_404(self) -> None:
        with self.assertRaises(HTTPError) as context:
            urlopen(f"{self.stock_url}/stock/999")

        self.assertEqual(context.exception.code, 404)
        try:
            self.assertEqual(
                json.loads(context.exception.read()),
                {"error": "Product 999 not found"},
            )
        finally:
            context.exception.close()

    def test_product_service_returns_product(self) -> None:
        product_host, product_port = self.product_server.server_address
        with urlopen(f"http://{product_host}:{product_port}/products/123") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(
                json.loads(response.read()),
                {"id": 123, "name": "Laptop", "price": 4500.0},
            )

    def test_product_service_returns_404_for_missing_product(self) -> None:
        product_host, product_port = self.product_server.server_address
        with self.assertRaises(HTTPError) as context:
            urlopen(f"http://{product_host}:{product_port}/products/999")

        self.assertEqual(context.exception.code, 404)
        context.exception.close()


if __name__ == "__main__":
    unittest.main()
