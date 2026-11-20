import unittest

from src.linear_probing import LinearProbingHashTable
from src.shortener import Shortener


class ShortenerContractTests:
    table_factory = None

    def new_shortener(self):
        return Shortener(table_factory=self.table_factory)

    def test_shortens_and_expands_urls(self):
        shortener = self.new_shortener()
        url = "https://example.com/path"

        code = shortener.shorten(url)

        self.assertEqual(code, "0")
        self.assertEqual(shortener.expand(code), url)

    def test_repeated_url_returns_same_code(self):
        shortener = self.new_shortener()
        url = "https://example.com/"

        first_code = shortener.shorten(url)
        second_code = shortener.shorten(url)

        self.assertEqual(first_code, second_code)

    def test_different_urls_get_different_codes(self):
        shortener = self.new_shortener()

        first_code = shortener.shorten("https://example.com/1")
        second_code = shortener.shorten("https://example.com/2")

        self.assertNotEqual(first_code, second_code)

    def test_rejects_urls_without_http_scheme_or_hostname(self):
        shortener = self.new_shortener()
        for url in (
            "ftp://example.com/file",
            "https:///missing-host",
            "https://example.com/with space",
            "not a url",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_rejected_url_does_not_consume_a_code(self):
        shortener = self.new_shortener()

        first_code = shortener.shorten("https://example.com/first")
        with self.assertRaises(ValueError):
            shortener.shorten("https://example.com/invalid url")
        next_code = shortener.shorten("https://example.com/next")

        self.assertEqual(first_code, "0")
        self.assertEqual(next_code, "1")

    def test_unknown_code_returns_none(self):
        self.assertIsNone(self.new_shortener().expand("unknown"))


class ChainingShortenerTests(ShortenerContractTests, unittest.TestCase):
    pass


class LinearProbingShortenerTests(ShortenerContractTests, unittest.TestCase):
    table_factory = LinearProbingHashTable


if __name__ == "__main__":
    unittest.main()
