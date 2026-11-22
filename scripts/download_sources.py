"""Downloads the pages in data/sources.yaml and converts them to Markdown documents.

    python scripts/download_sources.py

- Company pages -> data/raw/<store>/<doc_id>.md     (gitignored)
- Legislation   -> data/legislation/<doc_id>.md     (official text, may be committed)

Polite by default: respects robots.txt and waits between requests.
"""

import sys
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

import requests
import yaml

from kobi_asistan.data.parsing import parse, to_markdown

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "kobi-support-assistant/0.1 (academic capstone project)"
DELAY_SECONDS = 2


def robots_allows(url: str) -> bool:
    parts = urlsplit(url)
    rp = urllib.robotparser.RobotFileParser(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        rp.read()
    except OSError:
        return True  # if robots.txt cannot be read, assume allowed
    return rp.can_fetch(USER_AGENT, url)


def fetch(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def process(source: dict, out_dir: Path) -> list[Path]:
    if not robots_allows(source["url"]):
        print(f"  SKIPPED (disallowed by robots.txt): {source['url']}")
        return []
    html = fetch(source["url"])
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for doc in parse(source["parser"], html, source["doc_id"]):
        path = out_dir / f"{doc.doc_id}.md"
        path.write_text(to_markdown(doc, source), encoding="utf-8")
        print(f"  {path.relative_to(ROOT)}  ({len(doc.sections)} sections)")
        written.append(path)
    return written


def main() -> int:
    config = yaml.safe_load((ROOT / "data" / "sources.yaml").read_text(encoding="utf-8"))
    errors = 0

    jobs = []
    for store in config.get("stores", []):
        for source in store["sources"]:
            jobs.append((source, ROOT / "data" / "raw" / store["id"]))
    for source in config.get("legislation", []):
        jobs.append((source, ROOT / "data" / "legislation"))

    for i, (source, out_dir) in enumerate(jobs):
        print(f"[{i + 1}/{len(jobs)}] {source['doc_id']}")
        try:
            process(source, out_dir)
        except Exception as exc:  # one broken source should not stop the rest
            errors += 1
            print(f"  ERROR: {exc}")
        time.sleep(DELAY_SECONDS)

    print("Done." if not errors else f"{errors} source(s) failed.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
