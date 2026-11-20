"""Measure separate-chaining comparisons at fixed load factors."""

import csv
import random
from pathlib import Path

from src.base62 import encode
from src.hash_table import HashTable


CAPACITY = 4093
LOAD_FACTORS = [step / 4 for step in range(1, 17)]
MISS_SAMPLES = 10_000
OUTPUT_DIR = Path(__file__).parent


def _random_url(generator: random.Random) -> str:
    token = encode(generator.getrandbits(64))
    return f"https://{token}.example.test/{token}"


def _bucket_index(table: HashTable, key: str) -> int:
    steps = table.hash_steps(key)
    return steps[-1][3] if steps else 0


def measure(load_factor: float) -> tuple[float, float, float]:
    item_count = round(load_factor * CAPACITY)
    actual_load_factor = item_count / CAPACITY
    table = HashTable(initial_capacity=CAPACITY, max_load_factor=None)
    generator = random.Random(2026)
    entries = []
    while len(entries) < item_count:
        key = _random_url(generator)
        if table.contains(key):
            continue
        value = len(entries)
        table.put(key, value)
        entries.append(key)

    buckets = table.bucket_items()
    successful_comparisons = 0
    for key in entries:
        chain = buckets[_bucket_index(table, key)]
        for comparisons, (stored_key, _) in enumerate(chain, start=1):
            if stored_key == key:
                successful_comparisons += comparisons
                break
        else:
            raise RuntimeError(f"inserted URL was not found: {key}")

    unsuccessful_comparisons = 0
    miss_generator = random.Random(2027)
    sampled_misses = 0
    while sampled_misses < MISS_SAMPLES:
        missing_key = _random_url(miss_generator)
        if table.contains(missing_key):
            continue
        unsuccessful_comparisons += len(
            buckets[_bucket_index(table, missing_key)]
        )
        sampled_misses += 1

    return (
        actual_load_factor,
        successful_comparisons / item_count,
        unsuccessful_comparisons / MISS_SAMPLES,
    )


def _write_csv(rows: list[tuple[float, float, float, float, float]]) -> None:
    output_path = OUTPUT_DIR / "results.csv"
    with output_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "load_factor",
                "successful_measured",
                "successful_theoretical",
                "unsuccessful_measured",
                "unsuccessful_theoretical",
            )
        )
        writer.writerows(rows)


def _write_svg(rows: list[tuple[float, float, float, float, float]]) -> None:
    width, height = 760, 460
    left, right, top, bottom = 72, 28, 48, 62
    plot_width = width - left - right
    plot_height = height - top - bottom
    maximum_y = 5

    def x_position(load_factor: float) -> float:
        return left + load_factor / 4 * plot_width

    def y_position(value: float) -> float:
        return top + (maximum_y - value) / maximum_y * plot_height

    series = (
        ("Successful measured", 1, "#1769aa", "solid"),
        ("Successful theory (1 + α/2)", 2, "#1769aa", "dashed"),
        ("Unsuccessful measured", 3, "#c62828", "solid"),
        ("Unsuccessful theory (α)", 4, "#c62828", "dashed"),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="380" y="25" text-anchor="middle" font-family="sans-serif" '
        f'font-size="17">Separate chaining comparisons (capacity {CAPACITY})</text>',
    ]

    for tick in range(6):
        y = y_position(tick)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" '
            'stroke="#dddddd"/>'
        )
        parts.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" '
            f'font-family="sans-serif" font-size="12">{tick}</text>'
        )
    for tick in range(5):
        x = x_position(tick)
        parts.append(
            f'<text x="{x:.1f}" y="{height-bottom+22}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="12">{tick}</text>'
        )
    parts.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" '
            'stroke="#333"/>',
            f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" '
            f'y2="{height-bottom}" stroke="#333"/>',
            f'<text x="22" y="{height/2}" transform="rotate(-90 22 {height/2})" '
            'text-anchor="middle" font-family="sans-serif" font-size="13">'
            'Average comparisons</text>',
            f'<text x="{left+plot_width/2}" y="{height-12}" text-anchor="middle" '
            'font-family="sans-serif" font-size="13">Load factor (α)</text>',
        )
    )

    for label, column, color, line_style in series:
        points = " ".join(
            f"{x_position(row[0]):.1f},{y_position(row[column]):.1f}" for row in rows
        )
        dash = ' stroke-dasharray="6 4"' if line_style == "dashed" else ""
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            f'stroke-width="2"{dash}/>'
        )
        legend_y = top + 16 * (series.index((label, column, color, line_style)) + 1)
        parts.append(
            f'<line x1="{width-238}" y1="{legend_y}" x2="{width-212}" '
            f'y2="{legend_y}" stroke="{color}" stroke-width="2"{dash}/>'
        )
        parts.append(
            f'<text x="{width-206}" y="{legend_y+4}" font-family="sans-serif" '
            f'font-size="11">{label}</text>'
        )

    parts.append("</svg>")
    (OUTPUT_DIR / "results.svg").write_text(
        "\n".join(parts) + "\n", encoding="utf-8"
    )


def main() -> None:
    rows = []
    for load_factor in LOAD_FACTORS:
        actual_load_factor, successful, unsuccessful = measure(load_factor)
        rows.append(
            (
                actual_load_factor,
                successful,
                1 + actual_load_factor / 2,
                unsuccessful,
                actual_load_factor,
            )
        )

    _write_csv(rows)
    _write_svg(rows)
    print(f"용량 {CAPACITY}, 삽입 URL 개수에 따른 적재율 실험")
    print("α | 성공 탐색 측정/이론 | 실패 탐색 측정/이론")
    for load, success, success_theory, failure, failure_theory in rows:
        print(
            f"{load:.2f} | {success:.3f}/{success_theory:.3f} | "
            f"{failure:.3f}/{failure_theory:.3f}"
        )
    print(
        "이론값은 키가 버킷에 균등하게 배치된다는 근사입니다. 유한한 표본과 "
        "Horner 해시에서 URL 키가 만드는 실제 분포·삽입 순서 때문에 측정값이 "
        "달라질 수 있습니다. α가 1을 넘어도 체이닝은 계속 저장할 수 있지만, "
        "평균 충돌 체인과 탐색 비용이 함께 커집니다."
    )


if __name__ == "__main__":
    main()
