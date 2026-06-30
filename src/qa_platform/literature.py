from __future__ import annotations

import html
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT_DIR / "docs"
LITERATURE_REVIEW_PATH = DOCS_DIR / "literature-review.md"


def load_literature_markdown() -> str:
    return LITERATURE_REVIEW_PATH.read_text(encoding="utf-8")


def render_markdown_document(title: str, eyebrow: str, markdown_text: str) -> str:
    body = markdown_to_html(markdown_text)
    safe_title = html.escape(title)
    safe_eyebrow = html.escape(eyebrow)
    return f"""<!DOCTYPE html>
<html lang="sv">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{safe_title}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f3ede2;
        --paper: rgba(255, 251, 245, 0.94);
        --ink: #201a16;
        --muted: #675b54;
        --accent: #a64524;
        --accent-2: #d4a257;
        --line: rgba(32, 26, 22, 0.12);
        --shadow: 0 22px 64px rgba(70, 42, 13, 0.12);
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(212, 162, 87, 0.24), transparent 28%),
          radial-gradient(circle at bottom right, rgba(166, 69, 36, 0.16), transparent 26%),
          var(--bg);
      }}

      main {{
        width: min(980px, calc(100% - 32px));
        margin: 0 auto;
        padding: 44px 0 64px;
      }}

      .masthead {{
        margin-bottom: 24px;
      }}

      .eyebrow {{
        margin: 0 0 10px;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-size: 0.78rem;
      }}

      h1 {{
        margin: 0;
        font-size: clamp(2.4rem, 5vw, 4.4rem);
        line-height: 0.94;
      }}

      .lede {{
        max-width: 68ch;
        margin: 16px 0 0;
        color: var(--muted);
        line-height: 1.65;
        font-size: 1.04rem;
      }}

      article {{
        padding: 28px;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: var(--paper);
        box-shadow: var(--shadow);
        backdrop-filter: blur(8px);
      }}

      article > :first-child {{
        margin-top: 0;
      }}

      h2, h3, h4 {{
        margin: 1.8em 0 0.65em;
        line-height: 1.15;
      }}

      p, li {{
        font-size: 1.03rem;
        line-height: 1.72;
      }}

      p {{
        margin: 0 0 1em;
      }}

      ul, ol {{
        margin: 0 0 1.1em 1.3em;
        padding: 0;
      }}

      code {{
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
        font-size: 0.92em;
        background: rgba(32, 26, 22, 0.06);
        border-radius: 6px;
        padding: 0.08em 0.36em;
      }}

      table {{
        width: 100%;
        border-collapse: collapse;
        margin: 1.4em 0;
        overflow: hidden;
        border-radius: 18px;
      }}

      th, td {{
        padding: 14px 16px;
        border: 1px solid var(--line);
        vertical-align: top;
        text-align: left;
      }}

      th {{
        background: rgba(166, 69, 36, 0.08);
      }}

      a {{
        color: var(--accent);
      }}

      @media (max-width: 720px) {{
        main {{
          width: min(100% - 20px, 980px);
          padding-top: 24px;
        }}

        article {{
          padding: 18px;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      <header class="masthead">
        <p class="eyebrow">{safe_eyebrow}</p>
        <h1>{safe_title}</h1>
      </header>
      <article>
        {body}
      </article>
    </main>
  </body>
</html>
"""


def markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html_parts: list[str] = []
    paragraph: list[str] = []
    unordered_items: list[str] = []
    ordered_items: list[str] = []
    table_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph if part.strip())
            html_parts.append(f"<p>{_render_inline_markdown(text)}</p>")
            paragraph.clear()

    def flush_unordered() -> None:
        if unordered_items:
            items = "".join(f"<li>{_render_inline_markdown(item)}</li>" for item in unordered_items)
            html_parts.append(f"<ul>{items}</ul>")
            unordered_items.clear()

    def flush_ordered() -> None:
        if ordered_items:
            items = "".join(f"<li>{_render_inline_markdown(item)}</li>" for item in ordered_items)
            html_parts.append(f"<ol>{items}</ol>")
            ordered_items.clear()

    def flush_table() -> None:
        if not table_lines:
            return
        rows = [_parse_table_row(row) for row in table_lines]
        table_lines.clear()
        if len(rows) < 2:
            for row in rows:
                html_parts.append(f"<p>{_render_inline_markdown(' | '.join(row))}</p>")
            return
        header = rows[0]
        body_rows = rows[2:] if len(rows) > 2 and _is_table_divider(rows[1]) else rows[1:]
        head_html = "".join(f"<th>{_render_inline_markdown(cell)}</th>" for cell in header)
        body_html = "".join(
            "<tr>" + "".join(f"<td>{_render_inline_markdown(cell)}</td>" for cell in row) + "</tr>"
            for row in body_rows
        )
        html_parts.append(f"<table><thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table>")

    def flush_all() -> None:
        flush_paragraph()
        flush_unordered()
        flush_ordered()
        flush_table()

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            flush_unordered()
            flush_ordered()
            table_lines.append(stripped)
            continue
        flush_table()

        if not stripped:
            flush_paragraph()
            flush_unordered()
            flush_ordered()
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_unordered()
            flush_ordered()
            level = min(len(heading_match.group(1)) + 1, 6)
            content = _render_inline_markdown(heading_match.group(2).strip())
            html_parts.append(f"<h{level}>{content}</h{level}>")
            continue

        unordered_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if unordered_match:
            flush_paragraph()
            flush_ordered()
            unordered_items.append(unordered_match.group(1).strip())
            continue

        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ordered_match:
            flush_paragraph()
            flush_unordered()
            ordered_items.append(ordered_match.group(1).strip())
            continue

        paragraph.append(stripped)

    flush_all()
    return "\n".join(html_parts)


def _render_inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noreferrer">\1</a>', escaped)
    return escaped


def _parse_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip("|").split("|")]


def _is_table_divider(row: list[str]) -> bool:
    return all(cell and set(cell) <= {"-", ":", " "} for cell in row)
