"""Renders the newsletter Jinja2 template and inlines all CSS for email-client safety.

CLI: python tools/build_newsletter_html.py --content <path> --charts-manifest <path>
     --template <path> --output <path>
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from premailer import transform


def render_html(content: dict, chart_manifest: dict, template_path: Path) -> str:
    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.get_template(template_path.name)

    charts_by_id = {c["id"]: c for c in content.get("charts", []) if c["id"] in chart_manifest}

    return template.render(
        subject=content["subject"],
        preheader=content.get("preheader", ""),
        headline=content["headline"],
        sections=content.get("sections", []),
        charts_by_id=charts_by_id,
        sources=content.get("sources", []),
    )


def inline_css(html: str) -> str:
    return transform(html, remove_classes=False, keep_style_tags=False)


def build_newsletter_html(content_path: Path, manifest_path: Path, template_path: Path, output_path: Path) -> Path:
    content = json.loads(content_path.read_text(encoding="utf-8"))
    chart_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    html = render_html(content, chart_manifest, template_path)
    html = inline_css(html)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--charts-manifest", required=True, type=Path)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    output = build_newsletter_html(args.content, args.charts_manifest, args.template, args.output)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
