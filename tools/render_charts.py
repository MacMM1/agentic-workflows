"""Renders chart specs from a newsletter content JSON into static PNGs for email embedding.

CLI: python tools/render_charts.py --content <path> --output-dir <dir>
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CATEGORICAL_HUES = [
    "#2a78d6",  # slot 1: blue
    "#eb6834",  # slot 2: orange
    "#1baf7a",  # slot 3: aqua
    "#eda100",  # slot 4: yellow
    "#e87ba4",  # slot 5: magenta
    "#008300",  # slot 6: green
    "#4a3aa7",  # slot 7: violet
    "#e34948",  # slot 8: red
]
INK_PRIMARY = "#0b0b0b"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SUPPORTED_TYPES = {"bar", "line"}


def _validate_spec(spec: dict) -> str | None:
    """Returns an error message if the spec is invalid, else None."""
    if spec.get("type") not in SUPPORTED_TYPES:
        return f"unsupported chart type {spec.get('type')!r} (only {SUPPORTED_TYPES})"

    data = spec.get("data", {})
    categories = data.get("categories")
    series = data.get("series")
    if not categories or not series:
        return "missing data.categories or data.series"

    for s in series:
        values = s.get("values", [])
        if len(values) != len(categories):
            return f"series {s.get('name')!r} has {len(values)} values, expected {len(categories)}"
        if not all(isinstance(v, (int, float)) for v in values):
            return f"series {s.get('name')!r} has non-numeric values"

    return None


def render_chart(spec: dict, output_path: Path) -> None:
    plt.rcParams["font.family"] = "sans-serif"
    fig, ax = plt.subplots(figsize=(7, 3.9), dpi=160, facecolor="white")
    ax.set_facecolor("white")

    data = spec["data"]
    categories = data["categories"]
    series = data["series"]
    chart_type = spec["type"]

    if chart_type == "bar":
        n = len(series)
        width = 0.8 / n
        x = range(len(categories))
        for i, s in enumerate(series):
            offset = (i - (n - 1) / 2) * width
            xs = [xi + offset for xi in x]
            ax.bar(xs, s["values"], width=width, color=CATEGORICAL_HUES[i % len(CATEGORICAL_HUES)], label=s["name"])
        ax.set_xticks(list(x))
        ax.set_xticklabels(categories, color=INK_MUTED)
    else:  # line
        x = range(len(categories))
        for i, s in enumerate(series):
            ax.plot(x, s["values"], color=CATEGORICAL_HUES[i % len(CATEGORICAL_HUES)], label=s["name"], linewidth=2, marker="o", markersize=5)
        ax.set_xticks(list(x))
        ax.set_xticklabels(categories, color=INK_MUTED)

    ax.set_title(spec.get("title", ""), color=INK_PRIMARY, fontsize=13, pad=12, loc="left")
    if spec.get("x_label"):
        ax.set_xlabel(spec["x_label"], color=INK_MUTED, fontsize=10)
    if spec.get("y_label"):
        ax.set_ylabel(spec["y_label"], color=INK_MUTED, fontsize=10)

    ax.tick_params(colors=INK_MUTED, labelsize=9)
    ax.grid(axis="y", color=GRIDLINE, linewidth=1)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(GRIDLINE)

    if len(series) > 1:
        ax.legend(frameon=False, labelcolor=INK_MUTED, fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, facecolor="white")
    plt.close(fig)


def render_charts(content: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}

    for spec in content.get("charts", []):
        chart_id = spec.get("id", "unknown")
        error = _validate_spec(spec)
        if error:
            print(f"Warning: skipping chart {chart_id!r}: {error}")
            continue

        filename = f"{chart_id}.png"
        render_chart(spec, output_dir / filename)
        manifest[chart_id] = filename

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    content = json.loads(args.content.read_text(encoding="utf-8"))
    manifest = render_charts(content, args.output_dir)
    print(f"Rendered {len(manifest)} chart(s) to {args.output_dir}")


if __name__ == "__main__":
    main()
