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
            count = data.get('count', 0)
            
            # Clean terminal-derived artifacts (newlines in term names)
            term = term.replace('\n', ' ').strip()
            
            # --- HYBRID TAGGING SYSTEM (PHASE 10) ---
            
            # 1. Deterministic Heuristics (Regex/Lookup)
            heuristics = {
                'Historical Figure': r'\b(Bruno|Paracelsus|Boehme|Plotinus|Valentinus|Luria|Philo|Pythagoras|Empedocles|Burroughs|Augustine|Thomas|Socrates|Luther|Eckhart|Spinoza|Hegel)\b',
                'Theological Construct': r'\b(Anamnesis|Logos|Urgrund|Gnosis|Gnostic|Pleroma|Sophia|Ruah|Kyrios|Brahman|Christ|Saviour|Savior|Parousia|Karma|Karmic|Grace|Divine|God|Lord|Holy|Sacred|Agape|Caritas)\b',
                'Narrative Artifact': r'\b(Ubik|Stigmata|Tears|Scanner|Androids|Valis|Flow|Judo|Electric Ant|Frozen Journey|Deus Irae|Man in the High Castle)\b',
                'Visionary Experience': r'\b(2-74|3-74|Zebra|Sophia|St\. Sophia|Bathosphere|Xerox|Flash|Golden Section|Vast Active Living Intelligent System|Pink Light|Beam)\b',
                'Metaphysics': r'\b(Entropy|Time|Reality|Being|Space|Universe|Macrocosm|Microcosm|Matrix|Information|Ontological|Determinism|Necessity|Ananke|Force|Field)\b',
                'Technical Vocabulary': r'\b(Anamnesis|Entelechy|Sub specia aeternitatis|Syzygy|Protennoia|Aion|Eschaton|Dialectic|Synthesis|Thesis|Antithesis)\b'
            }
            
            assigned_category = "Unclassified"
            for cat, pattern in heuristics.items():
                if re.search(pattern, term, re.IGNORECASE):
                    assigned_category = cat
                    break
            
            # 2. Simulated LLM Refinement/Confirmation
            # (In a real scenario, the LLM would see the context and override the heuristic if needed)
            if assigned_category == "Unclassified":
                if "world" in term.lower() or "prison" in term.lower():
                    assigned_category = "Metaphysics"
                elif count > 50:
                    assigned_category = "Theological Construct"
                else:
                    assigned_category = "Technical Vocabulary"

            # Final Category Assignment
            final_category = assigned_category
            
            # Simple synthesis logic for the mock
            count = data.get('count', 0)
            passage_count = len(passages)
            
            # Heuristic definitions based on context and category
            if final_category == "Historical Figure":
                definition = f"A primary {final_category.lower()} in Dick's intellectual genealogy, treated as a historical precursor or psychic double."
            elif final_category == "Theological Construct":
                definition = f"A core {final_category.lower()} derived from Gnostic, Hermetic, or Christian traditions, repurposed for Dick's information-metaphysics."
            elif final_category == "Visionary Experience":
                definition = f"A technical or symbolic term describing the specific mechanics and phenomena of Dick's February/March 1974 awakening."
            else:
                definition = f"A recurring element in Dick's *Exegesis*, categorized as {final_category.lower()}, appearing approximately {count} times."

            # Specific Overrides for high-value terms
            if "gnosis" in term.lower():
                definition = "The concept of 'secret knowledge' or 'salvific insight' regarding the divine origin of the human soul and its entrapment in the material world."
            elif "bruno" in term.lower():
                definition = "Renaissance Hermeticist Giordano Bruno, whom Dick identifies as a primary historical precursor for his 2-74 awakening."
            elif "boehme" in term.lower():
                definition = "Jakob Boehme, German mystic whose dialectical theology influenced Dick's understanding of the *Urgrund* and the split in the godhead."
            elif "iron prison" in term.lower():
                definition = "The state of ontological entrapment in linear time and false reality (the 'Empire'), which Dick claims began to dissolve during his 2-74 experience."

            see_also_candidates = []
            for p in passages:
                if isinstance(p, dict):
                    co_ocs = p.get('co_occurrences', [])
                    if isinstance(co_ocs, list) and len(co_ocs) > 0:
                        see_also_candidates.append(str(co_ocs[0]))
            
            # Use explicit list slicing to satisfy linter
            unique_see_also = sorted(list(set(see_also_candidates)))
            final_see_also = unique_see_also[:4] if len(unique_see_also) > 4 else unique_see_also

            entry = {
                "term": term,
                "category": final_category,
                "aliases": aliases,
                "definition": definition,
                "extended_definition": f"This element occupies a critical position in the {final_category.lower()} domain of Dick's later thought. Textual evidence suggests it functions as a bridge between abstract theory and personal visionary encounter.",
                "significance": f"Dick treats {term} as a high-confidence anchor for his developing system. Its frequent co-occurrence with the logos and the 2-74 experience highlights its functional centrality.",
                "caution": "Scholars should distinguish between Dick's idiosyncratic use of this term and its standard historical or theological lineage.",
                "see_also": final_see_also
            }
            inventory.append(entry)
            processed_count += 1
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Skipping malformed packet {p_file.name}: {e}")
            continue

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=4)

    # Also save as .js for local CORS bypass
    JS_OUTPUT = output_path.with_suffix(".js")
    with open(JS_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(f"window.EXEGESIS_DICTIONARY = {json.dumps(inventory, indent=4)};")

    print(f"Successfully enriched {len(inventory)} entries. Saved to {output_path} and {JS_OUTPUT}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich dictionary packets using synthesis (Mock Version).")
    parser.add_argument("--packets", default="data/intermediate/evidence_packets", help="Path to evidence packets.")
    parser.add_argument("--output", default="docs/assets/data/dictionary_expanded.json", help="Path to expanded JSON.")
    parser.add_argument("--limit", type=int, default=100, help="Number of entries to process.")
    args = parser.parse_args()
    
    enrich_dictionary(args.packets, args.output, args.limit)
