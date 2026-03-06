import json
import os
import re
import argparse
from pathlib import Path
import subprocess

def run_step(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error in step: {result.stderr}")
        return False
    print(result.stdout)
    return True

def build_static_site(data_dir, docs_dir):
    expanded_json = Path(data_dir) / 'dictionary_expanded.json'
    docs_path = Path(docs_dir)
    cards_path = docs_path / 'cards'
    
    cards_path.mkdir(parents=True, exist_ok=True)

    if not expanded_json.exists():
        print(f"Error: Dictionary {expanded_json} not found. Run enrichment first.")
        return

    with open(expanded_json, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # Base Template
    card_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Exegesis Portal</title>
    <link rel="stylesheet" href="../assets/css/styles.css">
</head>
<body class="card-page">
    <header>
        <a href="../index.html" class="back-link">&larr; Back to Index</a>
        <h1>{title}</h1>
        <span class="category">{category}</span>
    </header>
    
    <main>
        <section class="definitions">
            <h2>Definition</h2>
            <p class="short-def"><strong>{short_def}</strong></p>
            <div class="extended-def">{extended_def}</div>
        </section>

        <section class="significance">
            <h2>Significance</h2>
            <p>{significance}</p>
        </section>

        <section class="caution">
            <h2>Caution / Scholarly Note</h2>
            <p>{caution}</p>
        </section>

        <section class="related">
            <h2>See Also</h2>
            <ul>{related_links}</ul>
        </section>
        
        <section class="passages-container">
            <h2>Evidence Passages</h2>
            <iframe src="../passages/{slug}.html" class="passage-frame"></iframe>
        </section>
    </main>

    <footer>
        <p>Exegesis Knowledge Project &copy; 2026</p>
    </footer>
</body>
</html>
"""

    for entry in entries:
        slug = re.sub(r'[^a-z0-9]+', '_', entry['term'].lower()).strip('_')
        related_html = "".join([f'<li><a href="{re.sub(r"[^a-z0-9]+", "_", r.lower()).strip("_")}.html">{r}</a></li>' for r in entry['see_also']])
        
        html_content = card_template.format(
            title=entry['term'],
            category=entry['category'],
            short_def=entry['definition'],
            extended_def=entry['extended_definition'],
            significance=entry['significance'],
            caution=entry['caution'],
            related_links=related_html,
            slug=slug
        )
        
        with open(cards_path / f"{slug}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)

    # Generate Index
    index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PKD Exegesis Knowledge Portal</title>
    <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body>
    <header>
        <h1>Exegesis Knowledge Portal</h1>
        <p>A deterministic, evidence-backed reference system for Philip K. Dick's mystical journal.</p>
    </header>
    
    <main>
        <div class="search-container">
            <input type="text" id="entrySearch" placeholder="Search terms (e.g., Bruno, Logos)...">
        </div>
        
        <div class="grid" id="entryGrid">
            {cards_grid}
        </div>
    </main>

    <script src="assets/js/app.js"></script>
</body>
</html>
"""
    cards_grid_html = ""
    for entry in entries:
        slug = re.sub(r'[^a-z0-9]+', '_', entry['term'].lower()).strip('_')
        cards_grid_html += f"""
        <div class="card" data-title="{entry['term']}">
            <h3>{entry['term']}</h3>
            <p>{entry['definition']}</p>
            <a href="cards/{slug}.html" class="portal-btn">View Portal &rarr;</a>
        </div>
        """
    
    with open(docs_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_template.format(cards_grid=cards_grid_html))

    # Add .nojekyll
    (docs_path / '.nojekyll').touch()

    print(f"Build complete. Index and {len(entries)} cards generated in {docs_path}")

def main():
    parser = argparse.ArgumentParser(description="Master build script for the Exegesis Browser portal.")
    parser.add_argument("--root", default=".", help="Root directory of the repo.")
    parser.add_argument("--skip-pipeline", action="store_true", help="Skip the Python extraction steps, only build site.")
    args = parser.parse_args()
    
    root = Path(args.root).resolve()
    scripts = root / "scripts"
    
    if not args.skip_pipeline:
        print("--- RUNNING EXTRACTION PIPELINE ---")
        if not run_step(["python", str(scripts / "exegesis_extractor.py"), "--input", "data/raw/exegesis_ordered.txt"]): return
        if not run_step(["python", str(scripts / "exegesis_canonicalizer.py")]): return
        if not run_step(["python", str(scripts / "exegesis_evidence_generator.py")]): return
        if not run_step(["python", str(scripts / "exegesis_llm_enricher.py")]): return
    
    print("--- BUILDING STATIC SITE ---")
    build_static_site("docs/assets/data", "docs")
    
    print("--- APPLYING SITELINKS ---")
    run_step(["python", str(scripts / "site_hyperlinker.py")])

if __name__ == "__main__":
    main()
