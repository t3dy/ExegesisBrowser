import json
import re
import csv
from pathlib import Path

def segment_exegesis(input_file, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    segments = []
    current_segment = None
    
    # regex for structural markers: folder 01, Folder 01, File 01, Book 1, Part 1, vol 1
    # Improved pattern to catch more variations and clean up
    marker_pattern = re.compile(r'^\s*(folder|file|book|part|vol)\s+([0-9a-z\-]+)', re.IGNORECASE)
    
    content = []
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.readlines()

    for i, line in enumerate(content, 1):
        match = marker_pattern.match(line)
        if match:
            type_group = match.group(1).capitalize()
            val_group = match.group(2)
            
            if current_segment:
                current_segment['end_line'] = i - 1
            
            seg_id = f"SEG_{len(segments):04d}"
            current_segment = {
                'segment_id': seg_id,
                'name': f"{type_group} {val_group}",
                'type': type_group,
                'value': val_group,
                'start_line': i,
                'end_line': None
            }
            segments.append(current_segment)
    
    if current_segment:
        current_segment['end_line'] = len(content)
        
    # Validation and Stats
    final_segments = [s for s in segments if s['end_line'] and (s['end_line'] - s['start_line']) > 2]
    
    # Generate segment_manifest.csv
    manifest_path = output_path / 'segment_manifest.csv'
    with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['SegmentID', 'Name', 'Type', 'Value', 'StartLine', 'EndLine', 'Length'])
        for s in final_segments:
            writer.writerow([
                s['segment_id'], s['name'], s['type'], s['value'], 
                s['start_line'], s['end_line'], s['end_line'] - s['start_line']
            ])

    # Generate source_structure.json
    structure_path = output_path / 'source_structure.json'
    with open(structure_path, 'w', encoding='utf-8') as f:
        json.dump(final_segments, f, indent=4)

    # Generate placeholder segment_stats.json (to be populated in Stage 3)
    stats_path = output_path / 'segment_stats.json'
    stats = {s['segment_id']: {"term_density": 0, "priority_terms": []} for s in final_segments}
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=4)
        
    print(f"Segmented Exegesis into {len(final_segments)} major units.")
    print(f"Saved manifest to {manifest_path}, structure to {structure_path}, and stats to {stats_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/exegesis_ordered.txt")
    parser.add_argument("--output", default="data/intermediate")
    args = parser.parse_args()
    segment_exegesis(args.input, args.output)
