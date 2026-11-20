"""In-memory URL shortener backed by the project's hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable


class Shortener:
    def __init__(self):
        self._codes_by_url = HashTable()
        self._urls_by_code = HashTable()
        self._next_id = 0

    def shorten(self, url: str) -> str:
        if not isinstance(url, str) or any(character.isspace() for character in url):
            raise ValueError("url must be an absolute http(s) URL without whitespace")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
        except ValueError as error:
            raise ValueError("url must be a valid absolute http(s) URL") from error
        if parsed.scheme.lower() not in ("http", "https") or not hostname:
            raise ValueError("url must be an absolute http(s) URL with a hostname")

        existing_code = self._codes_by_url.get(url)
        if existing_code is not None:
            return existing_code

        code = encode(self._next_id)
        self._next_id += 1
        self._codes_by_url.put(url, code)
        self._urls_by_code.put(code, url)
        return code

    def expand(self, code: str) -> str | None:
        return self._urls_by_code.get(code)
