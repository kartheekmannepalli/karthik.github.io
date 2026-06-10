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


def render(groups: dict[str, list[dict]]) -> str:
    # General first, then the rest alphabetically.
    ordered = sorted(
        groups.keys(), key=lambda c: (c != ROOT_CATEGORY, c.lower())
    )
    total = sum(len(v) for v in groups.values())
    updated = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    sections = []
    for cat in ordered:
        items = groups[cat]
        cards = "\n".join(
            f'        <a class="card" href="{html.escape(it["href"])}">'
            f'<span class="card-title">{html.escape(it["title"])}</span>'
            f'<span class="card-path">{html.escape(it["href"])}</span></a>'
            for it in items
        )
        sections.append(
            f'''    <section class="group" data-group>
      <h2>{html.escape(cat)} <span class="count">{len(items)}</span></h2>
      <div class="cards">
{cards}
      </div>
    </section>'''
        )
    sections_html = "\n".join(sections)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dev Notes &amp; Cheat Sheets</title>
<style>
  :root {{
    --bg: #0f1117; --panel: #181b24; --border: #262b38;
    --text: #e6e9ef; --muted: #8b94a7; --accent: #6ea8fe;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }}
  header {{
    max-width: 1000px; margin: 0 auto; padding: 40px 20px 10px;
  }}
  h1 {{ margin: 0 0 6px; font-size: 28px; }}
  .sub {{ color: var(--muted); margin: 0 0 20px; font-size: 14px; }}
  .search {{
    width: 100%; padding: 12px 14px; font-size: 15px; color: var(--text);
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 10px; outline: none;
  }}
  .search:focus {{ border-color: var(--accent); }}
  main {{ max-width: 1000px; margin: 0 auto; padding: 10px 20px 60px; }}
  .group {{ margin-top: 34px; }}
  h2 {{
    font-size: 15px; text-transform: uppercase; letter-spacing: .06em;
    color: var(--muted); border-bottom: 1px solid var(--border);
    padding-bottom: 8px; display: flex; align-items: center; gap: 10px;
  }}
  .count {{
    font-size: 12px; background: var(--panel); border: 1px solid var(--border);
    color: var(--muted); border-radius: 20px; padding: 1px 9px;
    letter-spacing: 0;
  }}
  .cards {{
    display: grid; gap: 10px; margin-top: 14px;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  }}
  .card {{
    display: flex; flex-direction: column; gap: 4px; padding: 14px 16px;
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 10px; text-decoration: none; color: var(--text);
    transition: border-color .15s, transform .05s;
  }}
  .card:hover {{ border-color: var(--accent); }}
  .card:active {{ transform: scale(.99); }}
  .card-title {{ font-weight: 600; }}
  .card-path {{ font-size: 12px; color: var(--muted); word-break: break-all; }}
  footer {{
    max-width: 1000px; margin: 0 auto; padding: 0 20px 50px;
    color: var(--muted); font-size: 13px;
  }}
  .empty {{ color: var(--muted); padding: 30px 0; display: none; }}
</style>
</head>
<body>
  <header>
    <h1>Dev Notes &amp; Cheat Sheets</h1>
    <p class="sub">{total} pages &middot; updated {updated}</p>
    <input id="search" class="search" type="search" placeholder="Filter by title, category, or filename&hellip;" autofocus>
  </header>
  <main id="content">
{sections_html}
    <p class="empty" id="empty">No matches.</p>
  </main>
  <footer>
    Auto-generated from the repo on every push. Drop a new <code>.html</code> file
    in any folder and this page updates itself.
  </footer>
<script>
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
