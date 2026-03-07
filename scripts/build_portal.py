import json
import os
import re
import argparse
import shutil
from pathlib import Path
import subprocess

def run_step(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        print(f"Error in step: {cmd}")
        return False
    return True

def clean_docs(docs_dir):
    """Removes stale HTML files from cards and passages."""
    docs_path = Path(docs_dir)
    for sub in ['cards', 'passages']:
        sub_path = docs_path / sub
        if sub_path.exists():
            print(f"Cleaning {sub_path}...")
            shutil.rmtree(sub_path)
        sub_path.mkdir(parents=True, exist_ok=True)

def generate_passage_fragments(data_dir, docs_dir):
    """Converts JSON evidence packets into HTML fragments for iframes."""
    packets_path = Path("data/intermediate/evidence_packets")
    passages_docs_path = Path(docs_dir) / 'passages'
    passages_docs_path.mkdir(parents=True, exist_ok=True)

    # Blacklist internal terms
    blacklist_slugs = ["evidence_packet_index", "indexed_folder", "toso_folder"]

    if not packets_path.exists():
        print(f"Warning: Evidence packets directory {packets_path} not found.")
        return

    passage_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="../assets/css/styles.css">
    <style>
        body {{ background: transparent !important; color: #ccc; font-family: 'Inter', sans-serif; padding: 0; margin: 0; }}
        .passage-item {{ background: #1a1a1a; border-left: 3px solid var(--highlight); padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px; }}
        .passage-meta {{ font-size: 0.8rem; color: #888; margin-bottom: 0.5rem; font-family: monospace; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 0.9rem; line-height: 1.5; color: #e0e0e0; }}
        .co-occurrences {{ margin-top: 0.5rem; font-size: 0.8rem; font-style: italic; color: #555; }}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""

    for json_file in packets_path.glob("*.json"):
        if json_file.stem in blacklist_slugs: continue
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        content_html = ""
        if not data.get('passages'):
            content_html = "<p>No direct evidence passages found for this term.</p>"
        else:
            for p in data['passages']:
                co_html = f'<div class="co-occurrences">Co-occurrences: {", ".join(p["co_occurrences"])}</div>' if p.get('co_occurrences') else ""
                content_html += f"""
                <div class="passage-item">
                    <div class="passage-meta">Line {p['line_start']}-{p['line_end']} | {p['folder_id']} | Match: '{p['matched_alias']}'</div>
                    <pre>{p['excerpt']}</pre>
                    {co_html}
                </div>
                """
        
        slug = json_file.stem
        with open(passages_docs_path / f"{slug}.html", 'w', encoding='utf-8') as f:
            f.write(passage_template.format(content=content_html))

def build_static_site(data_dir, docs_dir):
    expanded_json = Path(data_dir) / 'dictionary_expanded.json'
    docs_path = Path(docs_dir)
    cards_path = docs_path / 'cards'
    
    # Clean up before build
    clean_docs(docs_dir)

    if not expanded_json.exists():
        print(f"Error: Dictionary {expanded_json} not found. Run enrichment first.")
        return

    # Generate Passage Fragments First
    print("Generating evidence passage fragments...")
    generate_passage_fragments(data_dir, docs_dir)

    with open(expanded_json, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # Blacklist internal terms
    blacklist = ["Evidence Packet Index", "Indexed Folder", "Toso Folder"]
    entries = [e for e in entries if e['term'] not in blacklist]

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
            short_def=entry.get('technical_definition', 'Concept derived from Gnostic or Christian traditions.'),
            extended_def=entry.get('interpretive_note', 'Textual evidence suggests functional centrality in Dick\'s visionary system.'),
            significance=entry.get('interpretive_note', 'Functional centrality in visionary system.'),
            caution="Scholars should distinguish Dick's use from standard historical lineage.",
            related_links=related_html,
            slug=slug
        )
        
        with open(cards_path / f"{slug}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)

    # Generate Index (Simplified logic, the layout is already robust)
    index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PKD Exegesis Knowledge Portal</title>
    <link rel="stylesheet" href="assets/css/styles.css?v=1.0.3">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <header>
        <h1>Exegesis Knowledge Portal</h1>
        <p>A computational commentary on Philip K. Dick's intellectual network.</p>
    </header>
    
    <main>
        <section class="scholarly-intro">
            <h2>The Information Metaphysics of Philip K. Dick</h2>
            <p>
                This portal provides a deterministic, evidence-backed reference system for Philip K. Dick's 
                <em>Exegesis</em>. Our methodology prioritizes strict corpus hygiene and models Dick's thought 
                as a bidirectional network of passages and conceptual units.
            </p>
        </section>

        <div class="tab-container">
            <button class="tab-btn active" onclick="switchTab('cards')">Relational Cards</button>
            <button class="tab-btn" onclick="switchTab('analytics')">Analytics Dashboard</button>
            <button class="tab-btn" onclick="switchTab('source')">Source Structure</button>
            <button class="tab-btn" onclick="switchTab('graph')">Knowledge Graph</button>
        </div>

        <div id="cards-view" class="view-active">
            <div id="filter-bar"></div>
            <div class="search-container">
                <input type="text" id="term-search" placeholder="Search concepts, figures, systems...">
            </div>
            <div class="cards-grid" id="cards-grid">
                {cards_grid}
            </div>
        </div>

        <div id="analytics-view" class="view-hidden">
            <div class="analytics-container">
                <div class="analytics-card"><h3>Top 10 Most Frequent Concepts</h3><canvas id="chart-top-terms"></canvas></div>
                <div class="analytics-card"><h3>Domain Distribution</h3><canvas id="chart-categories"></canvas></div>
                <div class="analytics-card"><h3>Key Historical Figures</h3><canvas id="chart-figures"></canvas></div>
                <div class="analytics-card"><h3>Theological / Metaphysical Themes</h3><canvas id="chart-themes"></canvas></div>
            </div>
        </div>

        <div id="source-view" class="view-hidden">
            <div class="source-browser">
                <div id="source-list" class="source-list"></div>
                <div id="segment-detail" class="segment-detail">
                    <p class="placeholder-msg">Select a segment to view scholarly analysis.</p>
                </div>
            </div>
        </div>

        <div id="graph-view" class="view-hidden">
            <div class="graph-explorer">
                <div class="graph-legend">
                    <h4>Relational Explorer</h4>
                    <div class="legend-item"><span class="node-color concept"></span> Concept</div>
                    <div class="legend-item"><span class="node-color passage"></span> Passage Unit</div>
                    <div id="graph-category-list"></div>
                </div>
                <div id="cy"></div>
                <div id="node-info" class="node-info-panel view-hidden">
                    <button class="close-btn" onclick="document.getElementById('node-info').classList.add('view-hidden')">&times;</button>
                    <div id="node-info-content"></div>
                </div>
            </div>
        </div>
    </main>
 
    <footer>
        <p>&copy; 2026 Exegesis Semantic Browser • <a href="https://github.com/t3dy/ExegesisBrowser" style="color:var(--highlight); text-decoration:none;">GitHub Repository</a></p>
    </footer>

    <script src="assets/data/dictionary_expanded.js"></script>
    <script src="assets/data/analytics_summary.js"></script>
    <script src="assets/data/graph_data.js"></script>
    <script src="assets/data/source_structure.js"></script>
    <script src="assets/data/segment_summaries.js"></script>
    <script src="assets/js/app.js"></script>
</body>
</html>
"""
    cards_grid_html = ""
    for entry in entries:
        slug = re.sub(r'[^a-z0-9]+', '_', entry['term'].lower()).strip('_')
        cards_grid_html += f"""
        <a href="cards/{slug}.html" class="card" data-title="{entry['term']}" data-category="{entry['category']}">
            <span class="category">{entry['category']}</span>
            <h3>{entry['term']}</h3>
            <p>{entry.get('technical_definition', 'Brief scholarly preview...')}</p>
        </a>
        """
    
    # Save index
    with open(docs_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_template.format(cards_grid=cards_grid_html))

    (docs_path / '.nojekyll').touch()
    print(f"Build complete. Index and {len(entries)} cards generated.")

def main():
    parser = argparse.ArgumentParser(description="Master build script for the Exegesis Browser portal.")
    parser.add_argument("--root", default=".", help="Root directory of the repo.")
    parser.add_argument("--skip-pipeline", action="store_true", help="Skip the Python extraction steps, only build site.")
    args = parser.parse_args()
    
    root = Path(args.root).resolve()
    scripts = root / "scripts"
    
    if not args.skip_pipeline:
        print("--- RUNNING EXTRACTION PIPELINE ---")
        run_step(["python", str(scripts / "exegesis_extractor.py"), "--input", "data/raw/exegesis_ordered.txt", "--whitelist", "data/raw/whitelist.json"])
        run_step(["python", str(scripts / "exegesis_canonicalizer.py")])
        run_step(["python", str(scripts / "exegesis_evidence_generator.py")])
        run_step(["python", str(scripts / "exegesis_llm_enricher.py")])
        run_step(["python", str(scripts / "generate_passage_graph.py")])
        run_step(["python", str(scripts / "generate_analytics_data.py")])
    
    print("--- BUILDING STATIC SITE ---")
    build_static_site("docs/assets/data", "docs")
    
    print("--- APPLYING SITELINKS ---")
    run_step(["python", str(scripts / "site_hyperlinker.py")])

if __name__ == "__main__":
    main()
