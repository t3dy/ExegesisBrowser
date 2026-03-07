import json
import os
import hashlib
from pathlib import Path
import argparse

def generate_graph(packet_dir, dictionary_file, output_file):
    packet_path = Path(packet_dir).resolve()
    dict_path = Path(dictionary_file).resolve()
    output_path = Path(output_file).resolve()
    
    if not packet_path.exists():
        print(f"Error: Packet directory {packet_path} not found.")
        return

    # 1. Load Dictionary for term metadata
    with open(dict_path, 'r', encoding='utf-8') as f:
        dictionary = {entry['term']: entry for entry in json.load(f)}

    nodes = []
    edges = []
    
    # Track unique passages to avoid duplicates and assign stable IDs
    passage_registry = {}
    
    # 2. Iterate through evidence packets
    packets = list(packet_path.glob("*.json"))
    print(f"Processing {len(packets)} packets to build graph...")

    for p_file in packets:
        try:
            with open(p_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            term = data.get('term', '').replace('\n', ' ').strip()
            if not term or term not in dictionary:
                continue
            
            # Add Term Node
            term_id = f"term_{hashlib.md5(term.encode()).hexdigest()[:8]}"
            nodes.append({
                "data": {
                    "id": term_id,
                    "label": term,
                    "type": "term",
                    "category": dictionary[term].get('category', 'Top Term'),
                    "count": data.get('count', 0)
                }
            })

            # 3. Process Passages for this term
            term_passages = data.get('passages', [])
            if isinstance(term_passages, list):
                for passage in term_passages:
                    if not isinstance(passage, dict):
                        continue
                    text = str(passage.get('text', ''))
                    line_start = passage.get('line_start', 0)
                    line_end = passage.get('line_end', 0)
                    line_range = f"{line_start}-{line_end}"
                    
                    # Hash text for stable passage identity
                    passage_hash = hashlib.md5(text.encode()).hexdigest()[:12]
                    passage_id = f"psg_{passage_hash}"
                    
                    if passage_id not in passage_registry:
                        passage_registry[passage_id] = {
                            "id": passage_id,
                            "label": f"Passage {line_range}",
                            "type": "passage",
                            "text": text[:200] + "...", # Snippet for the graph
                            "full_text": text,
                            "lines": line_range,
                            "terms": set()
                        }
                        nodes.append({
                            "data": passage_registry[passage_id]
                        })
                    
                    # Link Term <-> Passage
                    reg_entry = passage_registry[passage_id]
                    if isinstance(reg_entry, dict):
                        terms_set = reg_entry.get("terms")
                        if isinstance(terms_set, set):
                            terms_set.add(term)
                    
                    edges.append({
                        "data": {
                            "id": f"e_{term_id}_{passage_id}",
                            "source": term_id,
                            "target": passage_id,
                            "type": "mention"
                        }
                    })

        except Exception as e:
            print(f"Error processing {p_file.name}: {e}")

    # 4. Refine Passage Nodes (convert sets to lists for JSON)
    for node in nodes:
        node_data = node.get('data')
        if isinstance(node_data, dict) and node_data.get('type') == 'passage':
            terms = node_data.get('terms')
            if isinstance(terms, set):
                node_data['terms'] = list(terms)
                node_data['weight'] = len(node_data['terms'])

    # 5. Optional: Passage-to-Passage similarity (Shared terms >= 3)
    passage_ids = [str(n['data']['id']) for n in nodes if isinstance(n.get('data'), dict) and n['data'].get('type') == 'passage']
    for i in range(len(passage_ids)):
        for j in range(i + 1, len(passage_ids)):
            p1 = passage_registry.get(passage_ids[i])
            p2 = passage_registry.get(passage_ids[j])
            if isinstance(p1, dict) and isinstance(p2, dict):
                t1 = p1.get('terms')
                t2 = p2.get('terms')
                if isinstance(t1, list) and isinstance(t2, list):
                    shared = set(t1) & set(t2)
                    if len(shared) >= 3: # High similarity threshold
                        edges.append({
                            "data": {
                                "id": f"sim_{p1['id']}_{p2['id']}",
                                "source": p1['id'],
                                "target": p2['id'],
                                "type": "similarity",
                                "weight": len(shared)
                            }
                        })

    graph_data = {
        "nodes": nodes,
        "edges": edges
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=4)

    # Also save as .js for local CORS bypass
    JS_OUTPUT = output_path.with_suffix(".js")
    with open(JS_OUTPUT, 'w', encoding='utf-8') as f:
        # We wrap in a simple object because these graphs can be huge
        f.write(f"window.EXEGESIS_GRAPH = {json.dumps(graph_data, indent=4)};")

    print(f"Graph generated with {len(nodes)} nodes and {len(edges)} edges.")
    print(f"Saved to {output_path} and {JS_OUTPUT}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a bidirectional term-passage knowledge graph.")
    parser.add_argument("--packets", default="data/intermediate/evidence_packets", help="Path to evidence packets.")
    parser.add_argument("--dict", default="docs/assets/data/dictionary_expanded.json", help="Path to expanded dictionary.")
    parser.add_argument("--output", default="docs/assets/data/graph_data.json", help="Path to output graph JSON.")
    args = parser.parse_args()
    
    generate_graph(args.packets, args.dict, args.output)
