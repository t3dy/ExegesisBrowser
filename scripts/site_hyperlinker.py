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
        
        # Scan all HTML files in docs/
    for html_file in docs_path.rglob("*.html"):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # We only want to hyperlink in certain sections (e.g., <p>, <div class="extended-def">, etc.)
        # For simplicity in this script, we'll exclude blocks that shouldn't be touched.
        
        # 1. Protect <script>, <style>, <title>, <button>, <h1>, <h2> tags
        # We replace them with placeholders
        placeholders = []
        def hide_tags(match):
            placeholders.append(match.group(0))
            return f"__TAG_PLACEHOLDER_{len(placeholders)-1}__"
        
        protected_content = re.sub(r'<(script|style|title|button|h1|h2|h3|a)[^>]*>.*?</\1>', hide_tags, content, flags=re.DOTALL | re.IGNORECASE)
        
        # 2. Re-apply linking to the remaining content
        for t in all_terms[:100]:
            slug = term_to_slug.get(t.lower())
            if not slug: continue
            
            # Simple word boundary replacement
            pattern = rf'\b({re.escape(t)})\b'
            protected_content = re.sub(pattern, lambda m: f'<a href="cards/{slug}.html" class="exegesis-link">{m.group(0)}</a>', protected_content)

        # 3. Restore placeholders
        for i, tag in enumerate(placeholders):
            protected_content = protected_content.replace(f"__TAG_PLACEHOLDER_{i}__", tag)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(protected_content)

    print(f"Hyperlinked {len(all_terms)} possible terms across {docs_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperlink terms in the static site.")
    parser.add_argument("--docs", default="docs", help="Path to static site folder.")
    parser.add_argument("--data", default="docs/assets/data", help="Path to data folder.")
    args = parser.parse_args()
    
    hyperlink_site(args.docs, args.data)
