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

    # Blacklist internal terms
    blacklist = ["Evidence Packet Index", "Indexed Folder", "Toso Folder"]
    entries = [e for e in entries if e['term'] not in blacklist]

    # All terms and aliases (longest first)
    all_terms = sorted([e['term'] for e in entries] + list(alias_map.keys()), key=len, reverse=True)
    
    term_to_slug = {}
    for e in entries:
        slug = re.sub(r'[^a-z0-9]+', '_', e['term'].lower()).strip('_')
        term_to_slug[e['term'].lower()] = slug
    
    for alias, canonical in alias_map.items():
        if canonical.lower() in term_to_slug:
            term_to_slug[alias.lower()] = term_to_slug[canonical.lower()]

    # Scan all HTML files in docs/
    for html_file in docs_path.rglob("*.html"):
        # Determine depth relative to docs/
        rel_path = html_file.relative_to(docs_path)
        depth = len(rel_path.parts) - 1
        prefix = "../" * depth if depth > 0 else ""
        cards_prefix = f"{prefix}cards/" if depth == 0 else "" # If at root (index.html), link to cards/
        if depth > 0 and rel_path.parts[0] == "cards":
            cards_prefix = "" # If already in cards/, link directly
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Protect <script>, <style>, <title>, <button>, <h1>, <h2>, <a> tags
        placeholders = []
        def hide_tags(match):
            placeholders.append(match.group(0))
            return f"__TAG_PLACEHOLDER_{len(placeholders)-1}__"
        
        protected_content = re.sub(r'<(script|style|title|button|h1|h2|h3|a|iframe)[^>]*>.*?</\1>', hide_tags, content, flags=re.DOTALL | re.IGNORECASE)
        
        # 2. Re-apply linking to the remaining content
        # We use a larger chunk of terms now (or even all of them)
        for t in all_terms:
            slug = term_to_slug.get(t.lower())
            if not slug: continue
            
            # Simple word boundary replacement
            # Note: We must be careful not to double-link. 
            # We'll use a temporary placeholder for the link to avoid matching it in later loops.
            pattern = rf'\b({re.escape(t)})\b'
            
            # Context-aware path
            link_path = f"{cards_prefix}{slug}.html"
            
            protected_content = re.sub(pattern, lambda m: f'<a href="{link_path}" class="exegesis-link">{m.group(0)}</a>', protected_content)

        # 3. Restore placeholders
        for i, tag in enumerate(placeholders):
            protected_content = protected_content.replace(f"__TAG_PLACEHOLDER_{i}__", tag)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(protected_content)

    print(f"Hyperlinked {len(all_terms)} terms across {docs_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperlink terms in the static site.")
    parser.add_argument("--docs", default="docs", help="Path to static site folder.")
    parser.add_argument("--data", default="docs/assets/data", help="Path to data folder.")
    args = parser.parse_args()
    
    hyperlink_site(args.docs, args.data)
