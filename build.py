#!/usr/bin/env python3
"""Build idea feed: lined / receipt / textbook / card in dual columns."""

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

STYLES = ("lined", "receipt", "textbook", "card")
SHORT = ("receipt", "lined")
MID = ("lined", "receipt")
LONG = ("textbook", "lined")


@dataclass
class Note:
    slug: str
    date: str
    body_html: str
    text: str
    style: str


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


_IG_ICON = (
    '<svg class="link-ig__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path fill="currentColor" d="M7.5 2h9A5.5 5.5 0 0 1 22 7.5v9A5.5 5.5 0 0 1 16.5 22h-9A5.5 5.5 0 0 1 2 16.5v-9A5.5 5.5 0 0 1 7.5 2Zm0 1.75A3.75 3.75 0 0 0 3.75 7.5v9A3.75 3.75 0 0 0 7.5 20.25h9A3.75 3.75 0 0 0 20.25 16.5v-9A3.75 3.75 0 0 0 16.5 3.75h-9Zm9.75 1.5a1.125 1.125 0 1 1 0 2.25 1.125 1.125 0 0 1 0-2.25ZM12 7.25A4.75 4.75 0 1 1 12 16.75 4.75 4.75 0 0 1 12 7.25Zm0 1.75a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"/>'
    "</svg>"
)


def ig_chip(handle: str, label: str | None = None) -> str:
    handle = handle.strip().lstrip("@")
    text = html.escape(label or f"@{handle}")
    href = html.escape(f"https://www.instagram.com/{handle}/", quote=True)
    return (
        f'<a class="link-ig" href="{href}" target="_blank" '
        f'rel="noopener noreferrer">{_IG_ICON}<span>{text}</span></a>'
    )


def md_inline(text: str) -> str:
    parks: list[str] = []

    def park(html_snip: str) -> str:
        parks.append(html_snip)
        return f"\x00IG{len(parks) - 1}\x00"

    def park_ig(handle: str, label: str | None = None) -> str:
        return park(ig_chip(handle, label))

    text = re.sub(
        r"(?i)\binstagram\s*[·•:：]\s*@?([A-Za-z0-9._]+)",
        lambda m: park_ig(m.group(1)),
        text,
    )
    text = re.sub(
        r"(?i)\binstagram\s*は\s*@?([A-Za-z0-9._]+)\s*です。?",
        lambda m: park_ig(m.group(1)),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\((https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]+)/?)\)",
        lambda m: park_ig(m.group(3), m.group(1)),
        text,
    )

    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        lambda m: (
            f'<a href="{html.escape(m.group(2), quote=True)}" '
            f'rel="noopener noreferrer">{m.group(1)}</a>'
        ),
        text,
    )
    for i, snip in enumerate(parks):
        text = text.replace(f"\x00IG{i}\x00", snip)
    return text


_OL = re.compile(r"^(\d+)\.\s+(.*)$")
_UL = re.compile(r"^[-*]\s+(.*)$")
_BQ = re.compile(r"^>\s?(.*)$")
_HR = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")


def md_to_html(body: str) -> str:
    lines = body.splitlines()
    out: list[str] = []
    i = 0

    def flush_para(buf: list[str]) -> None:
        if not buf:
            return
        parts = [md_inline(s.strip()) for s in buf if s.strip()]
        if parts:
            out.append("<p>" + "<br />\n".join(parts) + "</p>")
        buf.clear()

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if _HR.fullmatch(stripped):
            out.append("<hr />")
            i += 1
            continue

        if stripped.startswith("### "):
            out.append(f"<h3>{md_inline(stripped[4:].strip())}</h3>")
            i += 1
            continue
        if stripped.startswith("## "):
            out.append(f"<h2>{md_inline(stripped[3:].strip())}</h2>")
            i += 1
            continue
        if stripped.startswith("# "):
            out.append(f"<h2>{md_inline(stripped[2:].strip())}</h2>")
            i += 1
            continue

        bq = _BQ.match(line)
        if bq:
            chunks: list[str] = []
            while i < len(lines):
                m = _BQ.match(lines[i].rstrip())
                if not m:
                    break
                chunks.append(m.group(1).strip())
                i += 1
            paras: list[list[str]] = []
            cur: list[str] = []
            for c in chunks:
                if not c:
                    if cur:
                        paras.append(cur)
                        cur = []
                    continue
                cur.append(c)
            if cur:
                paras.append(cur)
            inner = "".join(
                "<p>" + "<br />\n".join(md_inline(x) for x in p) + "</p>" for p in paras
            )
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        ol = _OL.match(stripped)
        if ol:
            items: list[str] = []
            while i < len(lines):
                m = _OL.match(lines[i].strip())
                if not m:
                    break
                items.append(f"<li>{md_inline(m.group(2).strip())}</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue

        ul = _UL.match(stripped)
        if ul:
            items = []
            while i < len(lines):
                m = _UL.match(lines[i].strip())
                if not m:
                    break
                items.append(f"<li>{md_inline(m.group(1).strip())}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue

        para_buf: list[str] = []
        while i < len(lines):
            s = lines[i].rstrip()
            st = s.strip()
            if not st:
                break
            if (
                _HR.fullmatch(st)
                or st.startswith("#")
                or _BQ.match(s)
                or _OL.match(st)
                or _UL.match(st)
            ):
                break
            para_buf.append(st)
            i += 1
        flush_para(para_buf)

    return "\n".join(out)


def stable_hash(s: str) -> int:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def pick_style(slug: str, text: str, forced: str | None) -> str:
    if forced and forced in STYLES:
        return forced
    n = len(text.strip())
    h = stable_hash(slug)
    if n < 40:
        return SHORT[h % len(SHORT)]
    if n < 160:
        return MID[h % len(MID)]
    return LONG[h % len(LONG)]


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
                style=pick_style(path.stem, plain, meta.get("style")),
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
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500&family=Noto+Serif+SC:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=ZCOOL+XiaoWei&display=swap" rel="stylesheet" />
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
</body>
</html>
"""


def render_card(n: Note) -> str:
    return f"""<article class="scrap scrap--{html.escape(n.style)}" data-style="{html.escape(n.style)}" data-slug="{html.escape(n.slug)}">
  <time class="scrap__date" datetime="{html.escape(n.date)}">{html.escape(n.date)}</time>
  <div class="scrap__body">{n.body_html}</div>
</article>"""


def render_index(notes: list[Note]) -> str:
    cards = "".join(render_card(n) for n in notes)
    if not cards:
        cards = '<p class="feed__empty">还没有念头。</p>'

    body = f"""
  <img class="desk__photo" src="/assets/idea-bg.jpeg" alt="" width="3600" height="2400" decoding="async" fetchpriority="high" />
  <main class="desk">
    <div class="feed wrap">
      {cards}
    </div>
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
