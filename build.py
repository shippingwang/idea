#!/usr/bin/env python3
"""Build a minimal idea timeline from notes/*.md."""

from __future__ import annotations

import html
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTES = ROOT / "notes"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

SITE_TITLE = "idea"
HOME_URL = "/"
BASE = "/idea"


@dataclass
class Note:
    slug: str
    date: str
    body_html: str
    text: str


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, body


def md_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" rel="noopener noreferrer">\1</a>',
        text,
    )
    return text


def md_to_html(body: str) -> str:
    blocks: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        if not buf:
            return
        para = " ".join(line.strip() for line in buf if line.strip())
        if para:
            blocks.append(f"<p>{md_inline(para)}</p>")
        buf = []

    for line in body.splitlines():
        if not line.strip():
            flush()
            continue
        buf.append(line)
    flush()
    return "\n".join(blocks)


def load_notes() -> list[Note]:
    notes: list[Note] = []
    for path in sorted(NOTES.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        plain = " ".join(line.strip() for line in body.splitlines() if line.strip())
        notes.append(
            Note(
                slug=path.stem,
                date=meta.get("date") or date.today().isoformat(),
                body_html=md_to_html(body),
                text=plain,
            )
        )
    notes.sort(key=lambda n: (n.date, n.slug), reverse=True)
    return notes


def shell(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <link rel="icon" href="/assets/favicon.png" type="image/png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Noto+Serif+SC:wght@400;600&family=ZCOOL+XiaoWei&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{BASE}/css/idea.css" />
</head>
<body>
  <header class="nav">
    <div class="wrap nav__inner">
      <a class="nav__brand" href="{HOME_URL}" aria-label="shippingwang">
        <img class="nav__mark" src="/assets/favicon.png" alt="" width="28" height="28" />
        <span class="nav__brand-text">shippingwang</span>
      </a>
      <nav class="nav__links" aria-label="primary">
        <a href="/research/">research</a>
        <a href="/book/">book</a>
        <a href="/life/">life</a>
        <a class="is-active" href="{BASE}/">idea</a>
      </nav>
    </div>
  </header>
  {body}
  <footer class="foot">
    <div class="wrap foot__inner">
      <span>shippingwang / idea</span>
      <a href="{HOME_URL}">home</a>
    </div>
  </footer>
  <script src="{BASE}/js/idea.js"></script>
</body>
</html>
"""


def render_index(notes: list[Note]) -> str:
    items: list[str] = []
    for n in notes:
        items.append(
            f"""<li class="thread__item reveal">
  <div class="thread__mark" aria-hidden="true"></div>
  <time class="thread__date" datetime="{html.escape(n.date)}">{html.escape(n.date)}</time>
  <div class="thread__body">{n.body_html}</div>
</li>"""
        )
    if not items:
        items.append('<li class="thread__empty">暂无念头。</li>')

    body = f"""
  <main class="page wrap">
    <header class="mast">
      <p class="mast__kicker">idea</p>
      <h1 class="mast__title">心生</h1>
      <p class="mast__lead">短念头，沿一条线落下。</p>
    </header>
    <ol class="thread">
      {"".join(items)}
    </ol>
  </main>
"""
    return shell(SITE_TITLE, body)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    if STATIC.is_dir():
        shutil.copytree(STATIC, DIST, dirs_exist_ok=True)

    notes = load_notes()
    write(DIST / "index.html", render_index(notes))
    print(f"built {len(notes)} notes → {DIST}")


if __name__ == "__main__":
    main()
