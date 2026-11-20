"""HTTP interface for the in-memory URL shortener."""

import argparse
import html
from collections.abc import Callable
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable
from src.shortener import Shortener

Table = HashTable | LinearProbingHashTable
TableFactory = Callable[[], Table]


class ShortenerRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, shortener: Shortener, **kwargs):
        self.shortener = shortener
        super().__init__(*args, **kwargs)

    def _send_html(self, status: int, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _render_form(self, *, error: str | None = None, code: str | None = None) -> str:
        message = ""
        if error is not None:
            message = f'<p role="alert">{html.escape(error)}</p>'
        if code is not None:
            safe_code = html.escape(code, quote=True)
            message = (
                f'<p>Short URL: <a href="/{safe_code}">/{safe_code}</a></p>'
            )
        return (
            "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
            "<title>URL shortener</title><h1>URL shortener</h1>"
            f"{message}<form method=\"post\" action=\"/\">"
            '<label>URL <input name="url" type="url" required></label>'
            '<button type="submit">Shorten</button></form>'
            '<p><a href="/table">Inspect hash table</a></p></html>'
        )

    def _render_table(self) -> str:
        table = self.shortener._codes_by_url
        is_linear = isinstance(table, LinearProbingHashTable)
        position_name = "Slot" if is_linear else "Bucket"
        rows = []
        for bucket_index, bucket in enumerate(table.bucket_items()):
            if not bucket:
                rows.append(f"<tr><td>{bucket_index}</td><td><em>empty</em></td></tr>")
                continue

            entries = []
            for url, code in bucket:
                trace = table.hash_steps(url)
                calculation = ["h0 = 0"]
                for step_number, (_, value, before, after) in enumerate(
                    trace, start=1
                ):
                    calculation.append(
                        f"h{step_number} = ({before} * 31 + {value}) "
                        f"% {table.capacity} = {after}"
                    )
                probe_trace = " &rarr; ".join(
                    str(index) for index in table.probe_trace(url)
                )
                if is_linear:
                    inspection = f"<p>Slots examined: {probe_trace}</p>"
                else:
                    inspection = (
                        f"<p>Nodes compared: {len(table.probe_trace(url))}</p>"
                    )
                entries.append(
                    "<li><code>"
                    f"{html.escape(url)}"
                    "</code> &rarr; <code>"
                    f"{html.escape(code)}"
                    "</code>"
                    f"{inspection}<ol>"
                    + "".join(
                        f"<li><code>{html.escape(line)}</code></li>"
                        for line in calculation
                    )
                    + "</ol></li>"
                )
            rows.append(
                f"<tr><td>{bucket_index}</td><td><ol>{''.join(entries)}</ol></td></tr>"
            )

        return (
            "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
            f"<title>{table.strategy.title()} inspection</title>"
            f"<h1>{table.strategy.title()} inspection</h1>"
            f"<p>Horner hashing with coefficient 31; capacity {table.capacity}.</p>"
            f"<table border=\"1\"><thead><tr><th>{position_name}</th>"
            "<th>Entries and Horner calculation</th></tr></thead><tbody>"
            f"{''.join(rows)}</tbody></table><p><a href=\"/\">Home</a></p></html>"
        )

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(200, self._render_form())
        elif path == "/table":
            self._send_html(200, self._render_table())
        elif path.startswith("/") and path.count("/") == 1:
            url = self.shortener.expand(path[1:])
            if url is None:
                self._send_html(404, "<!doctype html><title>Not found</title><h1>Not found</h1>")
                return
            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self._send_html(404, "<!doctype html><title>Not found</title><h1>Not found</h1>")

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/":
            self._send_html(404, "<!doctype html><title>Not found</title><h1>Not found</h1>")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_html(400, self._render_form(error="Invalid request body length."))
            return
        if content_length < 0:
            self._send_html(400, self._render_form(error="Invalid request body length."))
            return
        if content_length > 65_536:
            self._send_html(413, self._render_form(error="Request body is too large."))
            return

        body = self.rfile.read(content_length).decode("utf-8", errors="replace")
        url = next(
            (value for key, value in parse_qsl(body, keep_blank_values=True) if key == "url"),
            "",
        )
        try:
            code = self.shortener.shorten(url)
        except ValueError as error:
            self._send_html(400, self._render_form(error=str(error)))
            return
        self._send_html(200, self._render_form(code=code))


def create_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    shortener: Shortener | None = None,
    table_factory: TableFactory | None = None,
) -> ThreadingHTTPServer:
    active_shortener = shortener
    if active_shortener is None:
        active_shortener = Shortener(table_factory)
    handler = partial(
        ShortenerRequestHandler, shortener=active_shortener
    )
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--strategy", choices=("chaining", "linear"), default="chaining")
    args = parser.parse_args()

    table_factory = HashTable if args.strategy == "chaining" else LinearProbingHashTable
    server = create_server(args.host, args.port, table_factory=table_factory)
    print(f"Serving on http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
