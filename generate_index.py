#!/usr/bin/env python3
"""
Generate index.html for the dev-notes repo.

Scans the repository for .html files, groups them by their top-level
directory (files in the repo root go under "General"), pulls a readable
title from each file's <title> tag, and writes a single index.html
landing page with client-side search.

Run locally with:  python3 generate_index.py
It also runs automatically in CI on every push (see .github/workflows/).
"""

import datetime
import html
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "index.html"

# Files / dirs we never want to list.
EXCLUDE_FILES = {"index.html"}
EXCLUDE_DIRS = {".git", ".github", "node_modules"}
ROOT_CATEGORY = "General"

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def extract_title(path: Path) -> str:
    """Return the <title> text of an HTML file, or a prettified filename."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = TITLE_RE.search(text)
        if match:
            title = re.sub(r"\s+", " ", match.group(1)).strip()
            if title:
                # Decode entities (e.g. &amp;) so they aren't double-escaped
                # when the page is rendered.
                return html.unescape(title)
    except OSError:
        pass
    # Fallback: turn "my-cheat_sheet_1.html" into "My Cheat Sheet 1"
    stem = path.stem.replace("-", " ").replace("_", " ")
    return stem.title()


def collect() -> dict[str, list[dict]]:
    """Walk the repo and group html files by top-level directory."""
    groups: dict[str, list[dict]] = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            if not name.lower().endswith(".html"):
                continue
            if name in EXCLUDE_FILES and Path(dirpath) == ROOT:
                continue
            full = Path(dirpath) / name
            rel = full.relative_to(ROOT)
            parts = rel.parts
            category = parts[0] if len(parts) > 1 else ROOT_CATEGORY
            groups.setdefault(category, []).append(
                {
                    "title": extract_title(full),
                    "href": str(rel).replace(os.sep, "/"),
                }
            )
    for items in groups.values():
        items.sort(key=lambda x: x["title"].lower())
    return groups


# Accent colors cycled across categories (used for the dot + hover accent).
PALETTE = [
    "#6ea8fe", "#5ed3a8", "#f4a259", "#c98bdb",
    "#e06c75", "#56c8d8", "#e8c468", "#7e8cff",
]


def initials(name: str) -> str:
    words = [w for w in re.split(r"[\s/_-]+", name) if w]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def render(groups: dict[str, list[dict]]) -> str:
    # General first, then the rest alphabetically.
    ordered = sorted(
        groups.keys(), key=lambda c: (c != ROOT_CATEGORY, c.lower())
    )
    total = sum(len(v) for v in groups.values())
    updated = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%b %d, %Y"
    )

    sections = []
    for i, cat in enumerate(ordered):
        items = groups[cat]
        color = PALETTE[i % len(PALETTE)]
        cards = "\n".join(
            f'          <a class="card" href="{html.escape(it["href"])}">\n'
            f'            <span class="card-badge">{html.escape(initials(cat))}</span>\n'
            f'            <span class="card-body">'
            f'<span class="card-title">{html.escape(it["title"])}</span>'
            f'<span class="card-path">{html.escape(it["href"])}</span></span>\n'
            f'            <span class="card-arrow">&rarr;</span>\n'
            f'          </a>'
            for it in items
        )
        sections.append(
            f'''      <section class="group" data-group style="--cat: {color}">
        <h2><span class="dot"></span>{html.escape(cat)}<span class="count">{len(items)}</span></h2>
        <div class="cards">
{cards}
        </div>
      </section>'''
        )
    sections_html = "\n".join(sections)

    return f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Dev Notes &amp; Cheat Sheets</title>
<style>
  :root {{
    --bg: #0d0f15; --bg2: #11141d; --panel: #171b26; --panel-hover: #1d2330;
    --border: #252b3b; --text: #e8ebf2; --muted: #8a93a6; --accent: #6ea8fe;
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.25);
  }}
  html[data-theme="light"] {{
    --bg: #f5f6fa; --bg2: #eef0f6; --panel: #ffffff; --panel-hover: #ffffff;
    --border: #e2e5ee; --text: #1c2130; --muted: #66708a; --accent: #2f6fed;
    --shadow: 0 1px 2px rgba(20,30,60,.06), 0 10px 30px rgba(20,30,60,.08);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; color: var(--text); -webkit-font-smoothing: antialiased;
    background:
      radial-gradient(1100px 600px at 80% -10%, rgba(110,168,254,.10), transparent 60%),
      radial-gradient(900px 500px at -10% 0%, rgba(94,211,168,.08), transparent 55%),
      var(--bg);
    font: 16px/1.6 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }}
  .wrap {{ max-width: 1040px; margin: 0 auto; padding: 0 22px; }}
  header {{ padding: 56px 0 8px; }}
  .titlebar {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }}
  h1 {{
    margin: 0; font-size: 34px; font-weight: 800; letter-spacing: -.02em;
    background: linear-gradient(92deg, var(--text), var(--accent));
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .sub {{ color: var(--muted); margin: 10px 0 0; font-size: 14px; }}
  .sub b {{ color: var(--text); font-weight: 600; }}
  .theme-btn {{
    flex: none; cursor: pointer; width: 40px; height: 40px; border-radius: 10px;
    background: var(--panel); border: 1px solid var(--border); color: var(--text);
    font-size: 17px; line-height: 1; box-shadow: var(--shadow); transition: background .15s, transform .05s;
  }}
  .theme-btn:hover {{ background: var(--panel-hover); }}
  .theme-btn:active {{ transform: scale(.94); }}
  .searchwrap {{ position: sticky; top: 0; z-index: 5; padding: 18px 0 8px;
    background: linear-gradient(var(--bg) 70%, transparent); margin-top: 18px; }}
  .searchbox {{ position: relative; }}
  .searchbox svg {{ position: absolute; left: 15px; top: 50%; transform: translateY(-50%);
    width: 17px; height: 17px; color: var(--muted); pointer-events: none; }}
  .search {{
    width: 100%; padding: 13px 16px 13px 44px; font-size: 15px; color: var(--text);
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
    outline: none; box-shadow: var(--shadow); transition: border-color .15s, box-shadow .15s;
  }}
  .search::placeholder {{ color: var(--muted); }}
  .search:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(110,168,254,.18); }}
  main {{ padding: 8px 0 70px; }}
  .group {{ margin-top: 36px; }}
  h2 {{
    font-size: 13px; text-transform: uppercase; letter-spacing: .08em; font-weight: 700;
    color: var(--muted); margin: 0 0 16px; padding-bottom: 10px;
    border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px;
  }}
  .dot {{ width: 9px; height: 9px; border-radius: 50%; background: var(--cat);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--cat) 22%, transparent); flex: none; }}
  .count {{ margin-left: auto; font-size: 11px; font-weight: 600; letter-spacing: 0;
    background: color-mix(in srgb, var(--cat) 14%, transparent);
    color: var(--cat); border-radius: 20px; padding: 2px 10px; }}
  .cards {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); }}
  .card {{
    position: relative; display: flex; align-items: center; gap: 13px; padding: 15px 16px;
    background: var(--panel); border: 1px solid var(--border); border-radius: 13px;
    text-decoration: none; color: var(--text); box-shadow: var(--shadow); overflow: hidden;
    transition: transform .12s ease, border-color .15s, background .15s;
  }}
  .card::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background: var(--cat); opacity: 0; transition: opacity .15s; }}
  .card:hover {{ transform: translateY(-2px); border-color: color-mix(in srgb, var(--cat) 55%, var(--border));
    background: var(--panel-hover); }}
  .card:hover::before {{ opacity: 1; }}
  .card:active {{ transform: translateY(0); }}
  .card-badge {{ flex: none; width: 38px; height: 38px; border-radius: 10px; display: grid;
    place-items: center; font-size: 12px; font-weight: 700; letter-spacing: .02em;
    color: var(--cat); background: color-mix(in srgb, var(--cat) 15%, transparent);
    border: 1px solid color-mix(in srgb, var(--cat) 30%, transparent); }}
  .card-body {{ display: flex; flex-direction: column; gap: 3px; min-width: 0; }}
  .card-title {{ font-weight: 600; font-size: 14.5px; line-height: 1.35;
    overflow: hidden; text-overflow: ellipsis; }}
  .card-path {{ font-size: 11.5px; color: var(--muted); white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; }}
  .card-arrow {{ margin-left: auto; color: var(--muted); font-size: 16px; flex: none;
    opacity: 0; transform: translateX(-4px); transition: opacity .15s, transform .15s; }}
  .card:hover .card-arrow {{ opacity: 1; transform: translateX(0); color: var(--cat); }}
  .empty {{ color: var(--muted); padding: 50px 0; text-align: center; display: none; }}
  footer {{ color: var(--muted); font-size: 13px; padding: 0 0 56px; }}
  footer code {{ background: var(--panel); border: 1px solid var(--border);
    border-radius: 5px; padding: 1px 6px; font-size: 12px; }}
  @media (max-width: 540px) {{ h1 {{ font-size: 27px; }} header {{ padding-top: 38px; }} }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="titlebar">
        <div>
          <h1>Dev Notes &amp; Cheat Sheets</h1>
          <p class="sub"><b>{total}</b> pages &middot; <b>{len(ordered)}</b> categories &middot; updated {updated}</p>
        </div>
        <button class="theme-btn" id="theme" type="button" title="Toggle theme" aria-label="Toggle theme">&#9789;</button>
      </div>
    </header>
    <div class="searchwrap">
      <div class="searchbox">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
        <input id="search" class="search" type="search" placeholder="Filter by title, category, or filename&hellip;" autofocus>
      </div>
    </div>
    <main id="content">
{sections_html}
      <p class="empty" id="empty">No matches found.</p>
    </main>
    <footer>
      Auto-generated from the repo on every push &mdash; drop a new <code>.html</code> file
      in any folder and this page updates itself.
    </footer>
  </div>
<script>
  // Theme toggle (persists across visits).
  const root = document.documentElement;
  const themeBtn = document.getElementById('theme');
  const saved = localStorage.getItem('theme');
  if (saved) root.dataset.theme = saved;
  else if (window.matchMedia && matchMedia('(prefers-color-scheme: light)').matches) root.dataset.theme = 'light';
  const syncIcon = () => themeBtn.innerHTML = root.dataset.theme === 'light' ? '&#9728;' : '&#9789;';
  syncIcon();
  themeBtn.addEventListener('click', () => {{
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', root.dataset.theme);
    syncIcon();
  }});

  // Live search.
  const search = document.getElementById('search');
  const groups = [...document.querySelectorAll('[data-group]')];
  const empty = document.getElementById('empty');
  search.addEventListener('input', () => {{
    const q = search.value.trim().toLowerCase();
    let any = false;
    for (const g of groups) {{
      let shown = 0;
      const cat = g.querySelector('h2').textContent.toLowerCase();
      for (const card of g.querySelectorAll('.card')) {{
        const hit = !q || card.textContent.toLowerCase().includes(q) || cat.includes(q);
        card.style.display = hit ? '' : 'none';
        if (hit) shown++;
      }}
      g.style.display = shown ? '' : 'none';
      if (shown) any = true;
    }}
    empty.style.display = any ? 'none' : 'block';
  }});
  // Keyboard: press "/" to focus search.
  document.addEventListener('keydown', e => {{
    if (e.key === '/' && document.activeElement !== search) {{ e.preventDefault(); search.focus(); }}
  }});
</script>
</body>
</html>
'''


def main() -> None:
    groups = collect()
    OUTPUT.write_text(render(groups), encoding="utf-8")
    total = sum(len(v) for v in groups.values())
    print(f"Wrote {OUTPUT} ({total} pages across {len(groups)} categories)")


if __name__ == "__main__":
    main()
