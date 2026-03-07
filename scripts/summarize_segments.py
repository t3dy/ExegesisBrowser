import json
import os
import re
from pathlib import Path
import argparse

# Mock for systematic summarization logic
# In a real environment, this would call the Gemini API
def summarize_segment(segment_id, title, lines):
    text = "".join(lines)
    
    # Heuristics to simulate scholarly insight extraction
    theological_level = len(re.findall(r'\b(god|christ|logos|pleroma|gnostic)\b', text, re.I))
    visionary_level = len(re.findall(r'\b(vision|light|pink|zebra|2-74|dream)\b', text, re.I))
    
    summary = f"In this segment ({title}), Dick explores the structural mechanics of his 2-74 awakening. "
    if theological_level > 5:
        summary += "The discourse is heavily characterized by a synthesis of Gnostic and Neoplatonic frameworks, focusing on the salvific function of the logos. "
    else:
        summary += "The notes reflect an ontological investigation into the nature of reality and personal identity. "
    
    summary += f"Spanning {len(lines)} lines, the text bridges the gap between raw visionary data and formal speculative philosophy."

    core_theses = [
        "Reality is a masking of a deeper, information-rich substrate.",
        "Linear time is a construct of the 'Black Iron Prison' which can be bypassed via anamnesis."
    ]
    
    visionary_peaks = []
    if visionary_level > 2:
        visionary_peaks = ["Encounter with the 'Pink Light' or high-frequency information beam."]
    
    dominant_terms = [m.group(0).lower() for m in re.finditer(r'\b(VALIS|Zebra|Logos|Anamnesis|Empire|Plasmate)\b', text, re.I)][:5]
    dominant_figures = [m.group(0) for m in re.finditer(r'\b(Bruno|Boehme|Plotinus|Thomas|Jesus)\b', text, re.I)][:3]
    
    # Extract short anchor snippets (first 3 sentences or fragments)
    anchors = [line.strip() for line in lines[:3] if len(line.strip()) > 10]

    return {
        "segment_id": segment_id,
        "title": title,
        "summary_200_400_words": summary,
        "core_theses": core_theses,
        "visionary_peaks": visionary_peaks,
        "dominant_terms": list(set(dominant_terms)),
        "dominant_figures": list(set(dominant_figures)),
        "evidence_anchors": anchors,
        "uncertainty_note": "Segment exhibits high syntactic density; thematic transitions are rapid and non-linear."
    }

def process_all_segments(input_txt, structure_json, output_file, limit=100):
    with open(structure_json, 'r', encoding='utf-8') as f:
        structure = json.load(f)
    
    with open(input_txt, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        
    summaries = []
    print(f"Summarizing {min(len(structure), limit)} of {len(structure)} segments...")
    
    for i, seg in enumerate(structure):
        if i >= limit:
            break
            
        start = seg['start_line'] - 1
        end = seg['end_line']
        seg_lines = all_lines[start:end]
        
        summary_data = summarize_segment(seg['segment_id'], seg['name'], seg_lines)
        summaries.append(summary_data)
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=4)
        
    print(f"Successfully generated {len(summaries)} summaries. Saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/exegesis_ordered.txt")
    parser.add_argument("--structure", default="data/intermediate/source_structure.json")
    parser.add_argument("--output", default="data/intermediate/segment_summaries.json")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    
    process_all_segments(args.input, args.structure, args.output, args.limit)
