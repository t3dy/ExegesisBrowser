import json
from pathlib import Path

def consolidate_segments(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)
    
    consolidated = {}
    
    for s in segments:
        key = f"{s['type']} {s['value']}"
        if key not in consolidated:
            consolidated[key] = {
                'name': key,
                'type': s['type'],
                'value': s['value'],
                'start_line': s['start_line'],
                'end_line': s['end_line'],
                'segment_count': 1
            }
        else:
            # Update end line
            consolidated[key]['end_line'] = max(consolidated[key]['end_line'], s['end_line'])
            consolidated[key]['start_line'] = min(consolidated[key]['start_line'], s['start_line'])
            consolidated[key]['segment_count'] += 1
            
    # Convert to list and sort
    final_list = sorted(consolidated.values(), key=lambda x: x['start_line'])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, indent=4)
        
    print(f"Consolidated into {len(final_list)} major units. Saved to {output_file}")

if __name__ == "__main__":
    input_json = "data/intermediate/source_structure.json"
    output_json = "data/intermediate/source_structure_consolidated.json"
    consolidate_segments(input_json, output_json)
