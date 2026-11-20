"""Compare chaining and linear probing on identical deterministic key sets."""

import csv
import math
import random
from pathlib import Path
from textwrap import wrap

from src.base62 import encode
from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


CAPACITY = 1000
LOAD_FACTORS = [step / 10 for step in range(1, 10)]
MISS_SAMPLES = 10_000
OUTPUT_DIR = Path(__file__).parent


def measure(
    requested_load: float,
) -> tuple[float, float, float, float, float, float, float, float, float]:
    item_count = round(requested_load * CAPACITY)
    load_factor = item_count / CAPACITY
    chaining = HashTable(initial_capacity=CAPACITY, max_load_factor=None)
    linear = LinearProbingHashTable(
        initial_capacity=CAPACITY, max_load_factor=None
    )
    generator = random.Random(2026)
    entries = []
    while len(entries) < item_count:
        key = f"item-{encode(generator.getrandbits(64))}"
        if chaining.contains(key):
            continue
        value = len(entries)
        chaining.put(key, value)
        linear.put(key, value)
        entries.append(key)

    chaining_success = sum(len(chaining.probe_trace(key)) for key in entries)
    linear_success = sum(len(linear.probe_trace(key)) for key in entries)

    chaining_failure = 0
    linear_failure = 0
    for _ in range(MISS_SAMPLES):
        key = f"missing-{encode(generator.getrandbits(64))}"
        chaining_failure += len(chaining.probe_trace(key))
        linear_failure += len(linear.probe_trace(key))

    return (
        load_factor,
        chaining_success / item_count,
        1 + load_factor / 2,
        chaining_failure / MISS_SAMPLES,
        load_factor,
        linear_success / item_count,
        0.5 * (1 + 1 / (1 - load_factor)),
        linear_failure / MISS_SAMPLES,
        0.5 * (1 + 1 / (1 - load_factor) ** 2),
    )


def _write_csv(rows: list[tuple[float, ...]]) -> None:
    with (OUTPUT_DIR / "comparison_results.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "load_factor",
                "chaining_success_measured",
                "chaining_success_theoretical",
                "chaining_unsuccessful_measured",
                "chaining_unsuccessful_theoretical",
                "linear_success_measured",
                "linear_success_theoretical",
                "linear_unsuccessful_measured",
                "linear_unsuccessful_theoretical",
            )
        )
        writer.writerows(rows)


def _write_svg(rows: list[tuple[float, ...]]) -> None:
    width, height = 1000, 560
    left, right, top, bottom = 72, 350, 58, 64
    plot_width = width - left - right
    plot_height = height - top - bottom
    maximum_y = math.ceil(max(max(row[7], row[8]) for row in rows) / 10) * 10
    series = (
        ("Chaining successful measured", 1, "#1769aa", False),
        ("Chaining successful theory", 2, "#6baed6", True),
        ("Chaining unsuccessful measured", 3, "#c62828", False),
        ("Chaining unsuccessful theory", 4, "#ef9a9a", True),
        ("Linear successful measured", 5, "#2e7d32", False),
        ("Linear successful theory", 6, "#81c784", True),
        ("Linear unsuccessful measured", 7, "#ef6c00", False),
        ("Linear unsuccessful theory", 8, "#ffb74d", True),
    )

    def x_position(load_factor: float) -> float:
        return left + (load_factor - 0.1) / 0.8 * plot_width

    def y_position(value: float) -> float:
        return top + (maximum_y - value) / maximum_y * plot_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="27" text-anchor="middle" font-family="sans-serif" '
        'font-size="18">Hash table search cost: measurement and theory</text>',
    ]

    for tick in range(6):
        value = maximum_y * tick / 5
        y = y_position(value)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_width}" '
            f'y2="{y:.1f}" stroke="#dddddd"/>'
        )
        parts.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" '
            f'font-family="sans-serif" font-size="12">{value:.0f}</text>'
        )
    for tick in range(1, 10):
        load = tick / 10
        x = x_position(load)
        parts.append(
            f'<text x="{x:.1f}" y="{height-bottom+22}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="11">{load:.1f}</text>'
        )
    parts.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" '
            'stroke="#333"/>',
            f'<line x1="{left}" y1="{height-bottom}" '
            f'x2="{left+plot_width}" y2="{height-bottom}" stroke="#333"/>',
            f'<text x="22" y="{height/2}" transform="rotate(-90 22 {height/2})" '
            'text-anchor="middle" font-family="sans-serif" font-size="13">'
            'Average probes</text>',
            f'<text x="{left+plot_width/2}" y="{height-14}" text-anchor="middle" '
            'font-family="sans-serif" font-size="13">Load factor (α)</text>',
        )
    )

    for line_number, (label, column, color, dashed) in enumerate(series):
        points = " ".join(
            f"{x_position(row[0]):.1f},{y_position(row[column]):.1f}" for row in rows
        )
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            f'stroke-width="2"{dash}/>'
        )
        legend_y = top + 18 * (line_number + 1)
        parts.append(
            f'<line x1="{width-right+18}" y1="{legend_y}" '
            f'x2="{width-right+46}" y2="{legend_y}" stroke="{color}" '
            f'stroke-width="2"{dash}/>'
        )
        parts.append(
            f'<text x="{width-right+54}" y="{legend_y+4}" '
            f'font-family="sans-serif" font-size="11">{label}</text>'
        )

    parts.append("</svg>")
    (OUTPUT_DIR / "comparison_results.svg").write_text(
        "\n".join(parts) + "\n", encoding="utf-8"
    )


def _pdf_text(value: str) -> str:
    ascii_text = value.encode("ascii", "replace").decode("ascii")
    return ascii_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_page(lines: list[str], font_size: int, leading: int) -> bytes:
    commands = [
        "BT",
        f"/F1 {font_size} Tf",
        "48 750 Td",
        f"{leading} TL",
    ]
    commands.extend(f"({_pdf_text(line)}) Tj T*" for line in lines)
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    return (
        f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
        + stream
        + b"\nendstream"
    )


def _write_report_pdf(rows: list[tuple[float, ...]]) -> None:
    last = rows[-1]
    page_one = [
        "Hash Table Search Cost Report",
        "Separate Chaining vs Linear Probing",
        "",
        "Method",
        *wrap(
            "Both implementations used the same deterministic set of keys, a fixed "
            "capacity of 1000, and load factors from 0.1 through 0.9. Each load factor "
            "used 10,000 unsuccessful-search samples. A probe is a chain node "
            "comparison for chaining and a slot inspection for linear probing.",
            width=88,
        ),
        "",
        "Uniform-hashing estimates",
        "Chaining: successful ~ 1 + alpha/2; unsuccessful ~ alpha.",
        "Linear: successful ~ 0.5*(1 + 1/(1-alpha));",
        "         unsuccessful ~ 0.5*(1 + 1/(1-alpha)^2).",
        "",
        "Findings",
        *wrap(
            f"At alpha={last[0]:.1f}, chaining measured {last[1]:.3f} successful and "
            f"{last[3]:.3f} unsuccessful probes (theory {last[2]:.3f} and "
            f"{last[4]:.3f}). Linear probing measured {last[5]:.3f} and "
            f"{last[7]:.3f} (theory {last[6]:.3f} and {last[8]:.3f}).",
            width=88,
        ),
        *wrap(
            "Linear probing degrades sharply at high load because primary clustering "
            "creates long runs of occupied slots. Its unsuccessful-search result "
            "deviates most from the uniform-hashing estimate. Chaining remains close "
            "to its estimates across this run. Finite samples and the actual key "
            "distribution explain smaller differences from theory.",
            width=88,
        ),
        "",
        "Reproduce with: make compare",
        "The accompanying SVG plots all measured and theoretical series.",
    ]
    page_two = [
        "Measurements (measured / theoretical average probes)",
        "",
        "alpha | chain success | chain failure | linear success | linear failure",
        "------+---------------+---------------+----------------+---------------",
    ]
    page_two.extend(
        f"{row[0]:.1f}   | {row[1]:.3f} / {row[2]:.3f}   "
        f"| {row[3]:.3f} / {row[4]:.3f}   "
        f"| {row[5]:.3f} / {row[6]:.3f}    "
        f"| {row[7]:.3f} / {row[8]:.3f}"
        for row in rows
    )
    page_two.extend(
        (
            "",
            "Probe-count convention",
            *wrap(
                "A successful search counts comparisons up to and including the "
                "matching entry. A failed chaining search counts nodes visited; a "
                "failed linear search also counts the final empty slot that ends "
                "the search.",
                width=88,
            ),
            "",
            "Files: comparison_results.csv (data), comparison_results.svg (graph).",
        )
    )

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 7 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 7 0 R >> >> /Contents 6 0 R >>",
        _pdf_page(page_one, 10, 14),
        _pdf_page(page_two, 8, 13),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, content in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode("ascii"))
        pdf.extend(content)
        pdf.extend(b"\nendobj\n")

    cross_reference_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{cross_reference_offset}\n%%EOF\n".encode("ascii")
    )
    (OUTPUT_DIR / "comparison_report.pdf").write_bytes(pdf)


def main() -> None:
    rows = [measure(load) for load in LOAD_FACTORS]
    _write_csv(rows)
    _write_svg(rows)
    _write_report_pdf(rows)
    print("α | chaining success/failure | linear success/failure")
    for row in rows:
        print(
            f"{row[0]:.1f} | {row[1]:.3f}/{row[3]:.3f} "
            f"(theory {row[2]:.3f}/{row[4]:.3f}) | "
            f"{row[5]:.3f}/{row[7]:.3f} "
            f"(theory {row[6]:.3f}/{row[8]:.3f})"
        )
    print(
        "두 표는 동일한 키를 사용했습니다. 선형 탐지는 적재율이 높을 때 "
        "클러스터링 때문에 실패 탐색 비용이 급격히 커집니다. 이론식은 균등 "
        "해시 가정을 두므로 유한 표본에서는 측정값과 차이가 날 수 있습니다."
    )


if __name__ == "__main__":
    main()
