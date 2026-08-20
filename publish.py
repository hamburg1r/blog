#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 python3Packages.requests

import json
import os
import sys
from pathlib import Path

import requests
import subprocess

DEV_API_URL = "https://dev.to/api/articles"
METADATA_FILE = "devto_articles.json"


def find_git_root(initial_path: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=initial_path,
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Warning: Not in a Git repository from {initial_path}. Error: {e.stderr.strip()}", file=sys.stderr)
        return None


def load_metadata(base_path: Path):
    path = base_path / METADATA_FILE

    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_metadata(data, base_path: Path):
    path = base_path / METADATA_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def upload_article(markdown_file: Path):
    api_key = os.environ.get("DEVTO_API_KEY")

    if not api_key:
        raise RuntimeError("DEVTO_API_KEY environment variable is not set")

    content = markdown_file.read_text(encoding="utf-8")

    payload = {
        "article": {
            "body_markdown": content,
            "published": False,
        }
    }

    response = requests.post(
        DEV_API_URL,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    if not response.ok:
        print(response.text, file=sys.stderr)
    response.raise_for_status()
    return response.json()


def update_article(article_id: int, markdown_file: Path):
    api_key = os.environ.get("DEVTO_API_KEY")

    if not api_key:
        raise RuntimeError("DEVTO_API_KEY environment variable is not set")

    content = markdown_file.read_text(encoding="utf-8")

    payload = {
        "article": {
            "body_markdown": content,
            "published": False,
        }
    }

    response = requests.put(
        f"{DEV_API_URL}/{article_id}",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    if not response.ok:
        print(response.text, file=sys.stderr)
    response.raise_for_status()
    return response.json()


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <markdown-file>")
        sys.exit(1)

    markdown_file = Path(sys.argv[1])

    if not markdown_file.exists():
        print(f"File not found: {markdown_file}")
        sys.exit(1)

    git_root = find_git_root(markdown_file.resolve().parent)

    if git_root:
        metadata_base_path = git_root
        metadata_key = str(markdown_file.resolve().relative_to(git_root))
        print(f"Using Git repository root: {git_root} for metadata base path and {metadata_key} as key.")
    else:
        metadata_base_path = Path.cwd()
        metadata_key = str(markdown_file)
        print(f"No Git repository found. Using current working directory: {metadata_base_path} for metadata base path and {metadata_key} as key.")

    metadata = load_metadata(metadata_base_path)
    article_metadata = metadata.get(metadata_key)

    if article_metadata and "id" in article_metadata:
        article_id = article_metadata["id"]
        print(f"Updating existing article (ID: {article_id}): {markdown_file}")
        article = update_article(article_id, markdown_file)
        print(f"Updated: {markdown_file}")
    else:
        print(f"Uploading new article: {markdown_file}")
        article = upload_article(markdown_file)
        print(f"Uploaded: {markdown_file}")

    metadata[metadata_key] = {
        "id": article["id"],
        "title": article.get("title"),
        "url": article.get("url"),
        # "published": article.get("published"),
    }

    save_metadata(metadata, metadata_base_path)

    print(f"DEV Article ID: {article['id']}")
    print(f"Metadata saved to: {METADATA_FILE}")


if __name__ == "__main__":
    main()
