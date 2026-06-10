# Dev Notes & Cheat Sheets

A personal collection of HTML cheat sheets, interview guides, and system-design
write-ups, published as a static website via GitHub Pages.

**Live site:** `https://<your-username>.github.io/dev-notes/`

## How it works

The homepage (`index.html`) is generated automatically. A GitHub Actions
workflow scans the repo for every `.html` file, groups them by folder, pulls a
readable title from each file's `<title>` tag, and rebuilds the landing page —
then deploys the site. **Just add a `.html` file and push; the homepage updates
itself.** You never edit `index.html` by hand.

Files in the repo root are listed under **General**. Files inside a folder are
grouped under that folder's name (e.g. `System Design/`), so you can categorize
simply by moving a file into a directory.

## Adding a new page

1. Drop a new `.html` file anywhere in the repo (optionally inside a folder to
   categorize it).
2. Give it a `<title>` — that becomes the link text on the homepage.
3. Commit and push to `main`.

```bash
git add .
git commit -m "Add new cheat sheet"
git push
```

The Actions workflow regenerates `index.html` and redeploys within a minute or two.

## One-time GitHub Pages setup

In the repo on GitHub: **Settings → Pages → Build and deployment → Source →
GitHub Actions**. That's it — the included workflow handles building and
publishing. (You only do this once.)

## Regenerating the homepage locally

Optional — the CI does this for you, but to preview before pushing:

```bash
python3 generate_index.py
open index.html
```

## Repo layout

```
.
├── index.html              # auto-generated landing page (do not edit)
├── generate_index.py       # builds index.html from the .html files present
├── .github/workflows/      # CI: rebuild + deploy on every push
├── System Design/          # grouped on the homepage as "System Design"
└── *.html                  # everything in root, grouped as "General"
```

## Note on visibility

GitHub Pages sites are public to anyone with the URL. Keep anything sensitive
out of this repo (or use a private hosting option instead).
