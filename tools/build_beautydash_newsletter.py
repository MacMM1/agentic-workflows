"""Renders a Beauty Dash brand newsletter issue from a content JSON into email-safe HTML.

CLI: python tools/build_beautydash_newsletter.py --content <path> --output <path>
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from premailer import transform

TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_NAME = "beautydash_newsletter.html.jinja2"


def render_html(content: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template(TEMPLATE_NAME)
    return template.render(
        issue_number=content["issue_number"],
        headline=content["headline"],
        intro=content.get("intro", ""),
        updates=content.get("updates", []),
        voice_card=content.get("voice_card"),
    )


def build(content_path: Path, output_path: Path) -> Path:
    content = json.loads(content_path.read_text(encoding="utf-8"))
    html = render_html(content)
    html = transform(html, remove_classes=False, keep_style_tags=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    output = build(args.content, args.output)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
