import csv
import json
import os
import re
from pathlib import Path
import argparse
import sys

def compile_term_patterns(term, aliases):
    """Compile regex patterns for a term and its aliases for phrase-aware matching."""
    pats = []
    # Include the term itself and all aliases
    search_strings = [term] + [a.strip() for a in aliases if a.strip()]
    unique_strings = sorted(list(set(search_strings)), key=len, reverse=True)
    
    for s in unique_strings:
        # Match with word boundaries, case-insensitive
        pattern = re.compile(rf"(?<!\w){re.escape(s)}(?!\w)", re.IGNORECASE)
        pats.append((s, pattern))
    return pats

def get_folder_id(lines, current_idx):
    """Look backwards for a folder marker like 'Folder 1' or 'File 2'."""
    folder_pattern = re.compile(r'\b(Folder|File|Book|Vol|Part)\s+([A-Z0-9.\-]+)\b', re.IGNORECASE)
    # Search up to 100 lines back
    for i in range(current_idx, max(-1, current_idx - 100), -1):
        match = folder_pattern.search(lines[i])
        if match:
            return f"{match.group(1)} {match.group(2)}"
    return "Unknown"

def generate_evidence(canonical_csv, source_file, output_dir, max_terms=500, max_passages=20, context_lines=8):
    canonical_path = Path(canonical_csv).resolve()
    source_path = Path(source_file).resolve()
    output_path = Path(output_dir).resolve()
    
    output_path.mkdir(parents=True, exist_ok=True)

    if not canonical_path.exists():
        print(f"CRITICAL ERROR: Canonical CSV missing at {canonical_path}")
        sys.exit(1)
    if not source_path.exists():
        print(f"CRITICAL ERROR: Source text missing at {source_path}")
        sys.exit(1)

    # 1. Load Canonical Terms
    terms_data = []
    with open(canonical_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['Count'] = int(row['Count'])
            terms_data.append(row)

    # 2. Prepare Term Inventory and Patterns
    inventory = {}
    term_patterns = [] # List of (canonical_name, [(alias, regex)])
    
    selected_terms = terms_data[:max_terms]
    for t in selected_terms:
        name = t['Term']
        aliases = [a.strip() for a in t['Aliases'].split(',') if a.strip()]
        inventory[name] = {
            "term": name,
            "aliases": aliases,
            "category": t['Primary Category'],
            "count": t['Count'],
            "passages": []
        }
        term_patterns.append((name, compile_term_patterns(name, aliases)))

    # 3. Load Source Text
    print(f"Loading source text from {source_path}...")
    with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # 4. Extract Evidence
    # To optimize, we find all matches for all terms in one pass
    # Using window-based extraction
    print(f"Extracting evidence for {len(term_patterns)} terms...")
    
    num_lines = len(lines)
    for i in range(num_lines):
        line = lines[i]
        line_lower = line.lower()
        
        # Quick check: does this line contain any interesting capitalized words or common fragments?
        # This is a broad filter to speed up the regex pass.
        if not any(c.isupper() for c in line) and not any(x in line_lower for x in ['agnostic', 'christ', 'gnosis']):
            continue

        for canonical_name, patterns in term_patterns:
            # Skip if we already have enough passages for this term
            if len(inventory[canonical_name]['passages']) >= max_passages:
                continue
            
            for alias, pattern in patterns:
                match = pattern.search(line)
                if match:
                    # Found a hit! Build the context window.
                    start_idx = max(0, i - context_lines // 2)
                    end_idx = min(num_lines, i + context_lines // 2 + 1)
                    excerpt = "".join(lines[start_idx:end_idx]).strip()
                    
                    folder_id = get_folder_id(lines, i)
                    
                    # Store passage
                    passage = {
                        "line_start": start_idx + 1,
                        "line_end": end_idx,
                        "matched_alias": alias,
                        "folder_id": folder_id,
                        "excerpt": excerpt,
                        "co_occurrences": [] # To be filled in a second pass or check
                    }
                    
                    # Local co-occurrence check (for other selected terms)
                    excerpt_lower = excerpt.lower()
                    for other_name, other_patterns in term_patterns:
                        if other_name == canonical_name: continue
                        # Check if any pattern for the other term matches the excerpt
                        if any(op[1].search(excerpt) for op in other_patterns):
                            passage['co_occurrences'].append(other_name)
                    
                    inventory[canonical_name]['passages'].append(passage)
                    break # Stop checking other aliases for this term on this line

    # 5. Save Packets and Reports
    total_generated = 0
    zero_passages = 0
    report_data = []

    for name, data in inventory.items():
        slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        
        # JSON Packet
        with open(output_path / f"{slug}.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        # Markdown Review
        with open(output_path / f"{slug}.md", 'w', encoding='utf-8') as f:
            f.write(f"# Evidence Packet: {name}\n\n")
            f.write(f"- **Category**: {data['category']}\n")
            f.write(f"- **Total Mentions**: {data['count']}\n")
            f.write(f"- **Aliases**: {', '.join(data['aliases'])}\n\n")
            f.write("## Supporting Passages (Context Windows)\n\n")
            if not data['passages']:
                f.write("*No passages found with current matching criteria.*\n")
                zero_passages += 1
            for p in data['passages']:
                f.write(f"### Line {p['line_start']}-{p['line_end']} (Match: '{p['matched_alias']}')\n")
                f.write(f"**Folder**: {p['folder_id']}\n\n")
                f.write("```text\n")
                f.write(p['excerpt'])
                f.write("\n```\n")
                if p['co_occurrences']:
                    f.write(f"**Co-occurrences**: {', '.join(p['co_occurrences'])}\n")
                f.write("\n---\n")
        
        total_generated += 1
        report_data.append((name, len(data['passages'])))

    # Summary Index
    with open(output_path / "evidence_packet_index.json", 'w', encoding='utf-8') as f:
        json.dump({n: len(d['passages']) for n, d in inventory.items()}, f, indent=4)

    # Generation Report
    with open(output_path / "evidence_generation_report.md", 'w', encoding='utf-8') as f:
        f.write("# Evidence Generation Report\n\n")
        f.write(f"- **Total Packets Generated**: {total_generated}\n")
        f.write(f"- **Packets with Zero Passages**: {zero_passages}\n")
        f.write("\n## Top Evidence Clusters (Richest Terms)\n")
        for name, count in sorted(report_data, key=lambda x: x[1], reverse=True)[:50]:
            f.write(f"- **{name}**: {count} passages\n")

    print(f"Done. Generated {total_generated} packets. Check {output_path} for details.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Evidence Packet Builder")
    parser.add_argument("--canonical-csv", default="data/intermediate/canonical_terms.csv")
    parser.add_argument("--source-file", default="data/raw/exegesis_ordered.txt")
    parser.add_argument("--output-dir", default="data/intermediate/evidence_packets")
    parser.add_argument("--max-terms", type=int, default=500)
    parser.add_argument("--max-passages", type=int, default=20)
    parser.add_argument("--context-lines", type=int, default=8)
    args = parser.parse_args()

    generate_evidence(
        args.canonical_csv, 
        args.source_file, 
        args.output_dir, 
        args.max_terms, 
        args.max_passages, 
        args.context_lines
    )
