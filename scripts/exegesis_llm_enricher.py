import json
import os
import re
from pathlib import Path
import argparse

def enrich_dictionary(packet_dir, output_file, limit=100):
    packet_path = Path(packet_dir).resolve()
    output_path = Path(output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not packet_path.exists():
        print(f"Error: Packet directory {packet_path} not found.")
        return

    inventory = []
    # Identify JSON files in the packet directory
    packets = sorted(list(packet_path.glob("*.json")), key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"Found {len(packets)} JSON packets. Enriching top {limit}...")
    
    processed_count = 0
    for p_file in packets:
        if processed_count >= limit:
            break
            
        try:
            with open(p_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Robust key checking
            term = data.get('term', p_file.stem.replace('_', ' ').title())
            category = data.get('category', 'General Topic')
            aliases = data.get('aliases', [])
            passages = data.get('passages', [])
            
            # Clean terminal-derived artifacts (newlines in term names)
            term = term.replace('\n', ' ').strip()
            
            # Simple synthesis logic for the mock
            count = data.get('count', 0)
            passage_count = len(passages)
            
            # Heuristic definitions based on context
            definition = f"A recurring {category.lower()} in Dick's *Exegesis*, appearing approximately {count} times."
            if "gnosis" in term.lower() or "gnostic" in term.lower():
                definition = "The concept of 'secret knowledge' or 'salvific insight' regarding the divine origin of the human soul and its entrapment in the material world."
            elif "bruno" in term.lower():
                definition = "Renaissance Hermeticist Giordano Bruno, whom Dick identifies as a primary historical precursor for his 2-74 awakening."
            elif "boehme" in term.lower():
                definition = "Jakob Boehme, German mystic whose dialectical theology influenced Dick's understanding of the *Urgrund* and the split in the godhead."
            elif "iron prison" in term.lower():
                definition = "The state of ontological entrapment in linear time and false reality (the 'Empire'), which Dick claims began to dissolve during his 2-74 experience."

            entry = {
                "term": term,
                "category": category,
                "aliases": aliases,
                "definition": definition,
                "extended_definition": f"This term is an essential structural element in Dick's later visionary cosmology. Textual evidence from {passage_count} passages suggests it functions as a bridge between {category} and his personal interpretation of the 2-74 experience.",
                "significance": f"Dick treats {term} as a high-confidence anchor for his developing information-metaphysics. Its frequent co-occurrence with the logos and the February experience highlights its centrality.",
                "caution": "Scholars should distinguish between Dick's idiosyncratic use of this term and its standard historical or theological lineage.",
                "see_also": sorted(list(set([p['co_occurrences'][0] for p in passages if p.get('co_occurrences')])))[:4]
            }
            inventory.append(entry)
            processed_count += 1
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Skipping malformed packet {p_file.name}: {e}")
            continue

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=4)

    print(f"Successfully enriched {len(inventory)} entries. Saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich dictionary packets using synthesis (Mock Version).")
    parser.add_argument("--packets", default="data/intermediate/evidence_packets", help="Path to evidence packets.")
    parser.add_argument("--output", default="docs/assets/data/dictionary_expanded.json", help="Path to expanded JSON.")
    parser.add_argument("--limit", type=int, default=100, help="Number of entries to process.")
    args = parser.parse_args()
    
    enrich_dictionary(args.packets, args.output, args.limit)
