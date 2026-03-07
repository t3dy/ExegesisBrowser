import csv
import json
import os
import re
from pathlib import Path
import argparse

def canonicalize(input_file, output_dir):
    input_path = Path(input_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: Raw candidate CSV {input_path} not found.")
        return

    candidates = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['Count'] = int(row['Count'])
            candidates.append(row)

    # Alias Rules
    alias_map = {
        "Bohme": "Jakob Boehme",
        "Boehme": "Jakob Boehme",
        "Boheme": "Jakob Boehme",
        "Xtian": "Christian",
        "Xtians": "Christian",
        "Xtianity": "Christianity",
        "BIP": "Black Iron Prison",
        "2-74": "February 1974 Experience",
        "3-74": "March 1974 Experience",
        "Nag Hammadi Library": "Nag Hammadi",
        "NH": "Nag Hammadi",
        "Plotinian": "Plotinus",
        "Neoplatonism": "Plotinus",
        "Thoma": "Thomas",
        "Thomas'": "Thomas",
        "Dick's": "Dick",
        "Plasmate": "Plasmate",
    }

    names_ending_in_s = {'Thomas', 'Jesus', 'Dionysos', 'Pythagoras', 'Spinoza', 'Parmenides', 'Heraclitus', 'Dionysus', 'Asklepios', 'Zeus', 'James', 'Augustine', 'Erasmus'}
    
    canonical_data = {}

    candidates.sort(key=lambda x: x['Count'], reverse=True)

    for cand in candidates:
        term = cand['Term']
        target = alias_map.get(term, term)
        
        # Heuristic: Strip 's' for plurals if it's not a common name
        if target.endswith('s') and target not in names_ending_in_s:
            if any(c['Term'] == target[:-1] for c in candidates):
                target = target[:-1]

        if target not in canonical_data:
            canonical_data[target] = {
                'title': target,
                'count': 0,
                'aliases': set(),
                'categories': set(),
                'methods': set()
            }
        
        canonical_data[target]['count'] += cand['Count']
        if term != target:
            canonical_data[target]['aliases'].add(term)
        canonical_data[target]['categories'].add(cand['Category'])
        for m in cand['Methods'].split(','):
            canonical_data[target]['methods'].add(m.strip())

    # --- SCHOLARLY WEIGHTING (PHASE 12) ---
    CATEGORIES_WEIGHTS = {
        'Hermeticism / Magic': ['hermetic', 'hermes', 'trismegistus', 'theurgy', 'alchemy', 'alchemical', 'magical', 'renaissance magic', 'giordano bruno', 'ficino'],
        'Christian Theosophy': ['theosophy', 'boehme', 'jakob boehme', 'christian theosophy', 'monad', 'pleroma', 'sophia'],
        'Neoplatonism / Gnosticism': ['gnostic', 'gnosticism', 'neoplatonic', 'neoplatonism', 'plotinus', 'porphyry', 'iamblichus', 'proclus', 'demiurge', 'yaldabaoth', 'aeon', 'kenoma', 'archon'],
        'German Idealism': ['hegel', 'fichte', 'schelling', 'kant', 'german idealism', 'dialectic', 'absolute spirit'],
        'PKD Visionary': ['valis', 'zebra', 'plasmate', 'firebright', '3-74', '2-74', 'february 1974', 'march 1974'],
        'Information Metaphysics': ['information', 'metaphysics', 'entropy', 'stochastic', 'binary', 'code', 'signal', 'noise', 'logostelemetry'],
        'Identity / Persona': ['identity', 'persona', 'thomas', 'phil', 'personality', 'fragmentationed', 'mask'],
        'Time Metaphysics': ['time', 'linear', 'orthogonal', 'circular', 'eternal', 'chronos', 'kairos', 'anamnesis']
    }

    def calculate_scholarly_score(term, description):
        score = 0
        text = (term + " " + description).lower()
        matched_cats = []
        for cat, keywords in CATEGORIES_WEIGHTS.items():
            matches = [k for k in keywords if k in text]
            if matches:
                score += len(matches) * 2
                matched_cats.append(cat)
        return score, matched_cats

    # Final alias map for linking phase
    final_alias_to_canonical = {alias: canonical for canonical, data in canonical_data.items() for alias in data['aliases']}

    canonical_csv = output_path / 'canonical_terms.csv'
    with open(canonical_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Term', 'Count', 'Score', 'Thematic Categories', 'Primary Category', 'Aliases'])
        
        # Sort by score first, then count
        sorted_terms = []
        for term, data in canonical_data.items():
            # Get a sample description from aliases or term
            sample_desc = "" # We don't have the full description here, but we can use aliases
            score, themes = calculate_scholarly_score(term, " ".join(data['aliases']))
            data['scholarly_score'] = score
            data['thematic_categories'] = themes
            sorted_terms.append((term, data))

        sorted_terms.sort(key=lambda x: (x[1]['scholarly_score'], x[1]['count']), reverse=True)

        for term, data in sorted_terms:
            # Requirements: Port all terms, but rank by score
            categories = list(data['categories'])
            primary_cat = 'Unknown'
            if categories:
                # Prioritize 'Scholarly' categories if they exist
                scholarly_cats = [c for c in categories if c in {'Metaphysics', 'Theological Construct', 'Visionary Experience'}]
                primary_cat = scholarly_cats[0] if scholarly_cats else categories[0]
            
            writer.writerow([
                str(term), 
                str(data['count']), 
                str(data['scholarly_score']),
                ', '.join(data['thematic_categories']),
                str(primary_cat), 
                ', '.join(sorted(list(data['aliases'])))
            ])

    alias_json = output_path / 'alias_map.json'
    with open(alias_json, 'w', encoding='utf-8') as f:
        json.dump(final_alias_to_canonical, f, indent=4)

    print(f"Canonicalized to {len(canonical_data)} terms. Saved to {canonical_csv} and {alias_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Canonicalize extracted terms and resolve aliases.")
    parser.add_argument("--input", default="data/intermediate/candidate_terms_raw.csv", help="Path to raw candidate CSV.")
    parser.add_argument("--output", default="data/intermediate", help="Path to intermediate output folder.")
    args = parser.parse_args()
    
    canonicalize(args.input, args.output)
