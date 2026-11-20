import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.linear_probing import LinearProbingHashTable
from src.server import create_server
from src.shortener import Shortener


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = Shortener()
        self.server = create_server("127.0.0.1", 0, self.shortener)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read()
        connection.close()
        return result

    def test_home_displays_url_form(self):
        status, _, body = self.request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn(b'<form method="post"', body)
        self.assertIn(b'name="url"', body)

    def test_valid_submission_displays_short_code(self):
        body = urlencode({"url": "https://example.com/path"})
        status, _, response_body = self.request(
            "POST",
            "/",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assertEqual(status, 200)
        self.assertIn(b'href="/0"', response_body)

    def test_invalid_submission_returns_bad_request(self):
        body = urlencode({"url": "ftp://example.com/"})
        status, _, response_body = self.request(
            "POST",
            "/",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assertEqual(status, 400)
        self.assertIn(b"http(s)", response_body)

    def test_short_code_redirects_and_unknown_code_is_not_found(self):
        url = "https://example.com/redirect"
        code = self.shortener.shorten(url)

        status, headers, _ = self.request("GET", f"/{code}")
        self.assertEqual(status, 302)
        self.assertEqual(dict(headers)["Location"], url)

        status, _, _ = self.request("GET", "/missing")
        self.assertEqual(status, 404)

    def test_table_page_shows_bucket_and_horner_calculation(self):
        first_url = "https://example.com/table-a"
        second_url = "https://example.com/table-i"
        first_code = self.shortener.shorten(first_url)
        second_code = self.shortener.shorten(second_url)
        table = self.shortener._codes_by_url
        self.assertEqual(
            table.hash_steps(first_url)[-1][3],
            table.hash_steps(second_url)[-1][3],
        )

        status, _, body = self.request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn(b"Bucket", body)
        self.assertIn(b"Horner", body)
        self.assertIn(b"h1 =", body)
        self.assertIn(b" * 31 + ", body)
        self.assertIn(first_url.encode(), body)
        self.assertIn(second_url.encode(), body)
        self.assertIn(b"URL key:", body)
        self.assertIn(b"Short code:", body)
        self.assertIn(b"Short link:", body)
        self.assertIn(f'href="/{first_code}">'.encode(), body)
        self.assertIn(f'href="/{second_code}">'.encode(), body)
        self.assertIn(f"/{first_code}</a>".encode(), body)
        self.assertIn(f"/{second_code}</a>".encode(), body)
        self.assertEqual(body.count(b'class="hash-node"'), 2)
        self.assertEqual(body.count(b'class="chain-arrow"'), 2)
        self.assertEqual(body.count(b"<details>"), 2)
        self.assertIn(b"<summary>Horner hash calculation</summary>", body)

    def test_linear_table_page_shows_wraparound_and_horner_calculation(self):
        linear_shortener = Shortener(LinearProbingHashTable)
        table = linear_shortener._codes_by_url
        urls = []
        candidate = 0
        while len(urls) < 3:
            url = f"https://example.com/wrap-{candidate}"
            if table.hash_steps(url)[-1][3] == 7:
                urls.append(url)
            candidate += 1
        for url in urls:
            linear_shortener.shorten(url)

        server = create_server("127.0.0.1", 0, linear_shortener)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_port
            )
            connection.request("GET", "/table")
            response = connection.getresponse()
            status = response.status
            body = response.read()
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

        self.assertEqual(status, 200)
        self.assertIn(b"Linear Probing inspection", body)
        self.assertIn(b"Slot", body)
        self.assertIn(b"Slots examined: 7 &rarr; 0 &rarr; 1", body)
        self.assertIn(b"Horner hash calculation", body)
        self.assertIn(b"h1 =", body)
        for url in urls:
            self.assertIn(url.encode(), body)


if __name__ == "__main__":
    unittest.main()
