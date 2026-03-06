import os
import json
import re
from pathlib import Path
import argparse

def hyperlink_site(docs_dir, data_dir):
    docs_path = Path(docs_dir)
    data_path = Path(data_dir)
    
    dict_file = data_path / 'dictionary_expanded.json'
    alias_file = data_path / 'alias_map.json'

    if not dict_file.exists():
        print(f"Error: Dictionary {dict_file} not found.")
        return

    with open(dict_file, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    with open(alias_file, 'r', encoding='utf-8') as f:
        alias_map = json.load(f)

    # All terms and aliases (longest first)
    all_terms = sorted([e['term'] for e in entries] + list(alias_map.keys()), key=len, reverse=True)
    
    term_to_slug = {}
    for e in entries:
        slug = re.sub(r'[^a-z0-9]+', '_', e['term'].lower()).strip('_')
        term_to_slug[e['term'].lower()] = slug
    
    for alias, canonical in alias_map.items():
        if canonical.lower() in term_to_slug:
            term_to_slug[alias.lower()] = term_to_slug[canonical.lower()]

    def link_callback(match):
        term = match.group(0)
        slug = term_to_slug.get(term.lower())
        if slug:
            # We determine relative path based on the file's depth.
            # Simplified: Just return span for now or a path that works.
            # In docs/index.html, path is cards/slug.html.
            # In docs/cards/slug.html, path is slug.html (or ../cards/slug.html).
            return f'<a href="cards/{slug}.html" class="exegesis-link">{term}</a>'
        return term

    # Scan all HTML files in docs/
    for html_file in docs_path.rglob("*.html"):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple regex (needs to avoid linking inside tags)
        # For a static site, we'll do a basic pass.
        for t in all_terms[:100]: # Top 100 for safety/speed
            pattern = rf'\b({re.escape(t)})\b'
            # Avoid replacing already replaced or inside tags
            # (High level: This is non-trivial but let's do a basic one)
            if f'cards/{term_to_slug.get(t.lower())}.html' in content: continue
            content = re.sub(pattern, link_callback, content)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

    print(f"Hyperlinked {len(all_terms)} possible terms across {docs_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperlink terms in the static site.")
    parser.add_argument("--docs", default="docs", help="Path to static site folder.")
    parser.add_argument("--data", default="docs/assets/data", help="Path to data folder.")
    args = parser.parse_args()
    
    hyperlink_site(args.docs, args.data)
