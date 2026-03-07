import json
import os
from pathlib import Path
from collections import Counter

# Path Configuration
BASE_DIR = Path(r"C:\Users\PC\Downloads\ExegesisBrowser")
STATS_FILE = Path(r"C:\Users\PC\Downloads\Exegesis_Analysis_Results\global_stats.json")
DICT_FILE = BASE_DIR / "docs" / "assets" / "data" / "dictionary_expanded.json"
OUTPUT_FILE = BASE_DIR / "docs" / "assets" / "data" / "analytics_summary.json"

def generate_analytics():
    print("--- GENERATING ANALYTICS DATA ---")
    
    if not STATS_FILE.exists():
        print(f"Error: {STATS_FILE} not found.")
        return

    with open(STATS_FILE, "r", encoding="utf-8") as f:
        stats = json.load(f)

    if not DICT_FILE.exists():
        print(f"Error: {DICT_FILE} not found.")
        return

    with open(DICT_FILE, "r", encoding="utf-8") as f:
        dictionary = json.load(f)

    # Map terms to their categories for accurate categorization
    term_to_category = {item["term"]: item["category"] for item in dictionary}
    
    # 1. Top Terms Overall (combining categories)
    all_counts = {}
    all_counts.update(stats.get("figures", {}))
    all_counts.update(stats.get("topics", {}))
    # Filter out low-value candidates and align with dictionary
    for k, v in stats.get("new_candidates", {}).items():
        if k in term_to_category:
            all_counts[k] = max(all_counts.get(k, 0), v)

    top_15_overall = dict(Counter(all_counts).most_common(15))

    # 2. Top Historical Figures
    figures_only = {k: v for k, v in all_counts.items() if term_to_category.get(k) == "Historical Figure"}
    top_10_figures = dict(Counter(figures_only).most_common(10))

    # 3. Category Distribution
    category_counts = Counter()
    for item in dictionary:
        category_counts[item["category"]] += 1
    
    # 4. Top Metaphysics/Theological Terms
    themes_only = {k: v for k, v in all_counts.items() if term_to_category.get(k) in ["Metaphysics", "Theological Construct"]}
    top_10_themes = dict(Counter(themes_only).most_common(10))

    summary = {
        "top_overall": top_15_overall,
        "top_figures": top_10_figures,
        "top_themes": top_10_themes,
        "category_distribution": dict(category_counts),
        "total_terms": len(dictionary),
        "total_mentions": sum(all_counts.values())
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    
    # Also save as .js for local CORS bypass
    JS_OUTPUT = OUTPUT_FILE.with_suffix(".js")
    with open(JS_OUTPUT, "w", encoding="utf-8") as f:
        f.write(f"window.EXEGESIS_ANALYTICS = {json.dumps(summary, indent=4)};")
    
    print(f"Analytics summary saved to {OUTPUT_FILE} and {JS_OUTPUT}")

if __name__ == "__main__":
    generate_analytics()
