import os
import re
import collections
import csv
from pathlib import Path
import argparse

def extract_candidates(input_file, output_dir, review_dir):
    input_path = Path(input_file)
    output_path = Path(output_dir)
    review_path = Path(review_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    review_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: Input file {input_path} not found.")
        return

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # 1. Capitalized Multi-word Phrases (2-4 words)
    stop_words = {
        'The', 'A', 'An', 'In', 'On', 'At', 'By', 'To', 'From', 'With', 'And', 'But', 'Or', 'Yet', 'So', 'For', 
        'It', 'He', 'She', 'They', 'We', 'I', 'You', 'My', 'Your', 'His', 'Her', 'This', 'That', 'What', 'When', 
        'Where', 'How', 'Which', 'Who', 'Whom', 'Whose', 'Why', 'There', 'Then', 'Here', 'Now', 'Last', 'Next',
        'Needs', 'Review', 'Note', 'Also', 'Thus', 'Hence', 'Every', 'Each', 'All', 'Some', 'Any', 'One', 'Two', 
        'First', 'Second', 'Third'
    }
    
    phrase_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b'
    phrases = re.findall(phrase_pattern, text)
    filtered_phrases = []
    for p in phrases:
        p_strip = p.strip()
        if p_strip == "Needs Review": continue
        if p_strip.split()[0] in stop_words: continue
        filtered_phrases.append(p_strip)
    
    phrase_counts = collections.Counter(filtered_phrases)

    # 2. Single Capitalized Words
    word_pattern = r'\b[A-Z][a-z]{3,}\b'
    words = re.findall(word_pattern, text)
    filtered_words = [w for w in words if w not in stop_words]
    word_counts = collections.Counter(filtered_words)

    # 3. Pattern Matching: "the X of Y"
    of_pattern = r'\bthe\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+of\s+([A-Z][a-z]+)\b'
    of_matches = re.findall(of_pattern, text)
    of_phrases = [f"{m[0]} of {m[1]}" for m in of_matches]
    of_counts = collections.Counter(of_phrases)

    # 4. Naming patterns: "called X", "name X", "person X"
    naming_pattern = r'\b(?:called|name|person|persona|entity)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    naming_matches = re.findall(naming_pattern, text)
    naming_counts = collections.Counter(naming_matches)

    # Consolidation
    all_candidates = {}

    def add_to_candidates(counter, category, method):
        for term, count in counter.items():
            if term not in all_candidates:
                all_candidates[term] = {'count': 0, 'category': category, 'methods': set()}
            all_candidates[term]['count'] += count
            all_candidates[term]['methods'].add(method)

    add_to_candidates(phrase_counts, 'Top Term', 'phrase_mining')
    add_to_candidates(word_counts, 'Top Term', 'word_mining')
    add_to_candidates(of_counts, 'Tradition/Theology', 'syntax_pattern')
    add_to_candidates(naming_counts, 'Persona', 'naming_pattern')

    # Filtering and Sorting
    results = []
    for term, data in all_candidates.items():
        if data['count'] > 10:
            results.append({
                'Term': term,
                'Count': data['count'],
                'Category': data['category'],
                'Methods': ", ".join(data['methods'])
            })
    
    results.sort(key=lambda x: x['Count'], reverse=True)

    # Save CSV
    csv_file = output_path / 'candidate_terms_raw.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Term', 'Count', 'Category', 'Methods'])
        writer.writeheader()
        writer.writerows(results)

    # Save Markdown Review
    md_file = review_path / 'candidate_terms_review.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# Exegesis Portal Candidate Discovery\n\n")
        f.write("## High Confidence Candidates\n")
        for r in results[:50]:
            f.write(f"- **{r['Term']}** ({r['Count']}) | {r['Category']} | Methods: {r['Methods']}\n")
        
        f.write("\n## New Phrasal Patterns found\n")
        for p, c in of_counts.most_common(20):
            f.write(f"- {p} ({c})\n")

    print(f"Extracted {len(results)} candidates. Saved to {csv_file} and {md_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract potential dictionary terms from text.")
    parser.add_argument("--input", default="data/raw/exegesis_ordered.txt", help="Path to raw source text.")
    parser.add_argument("--output", default="data/intermediate", help="Path to intermediate output folder.")
    parser.add_argument("--review", default="data/review", help="Path to review folder.")
    args = parser.parse_args()
    
    extract_candidates(args.input, args.output, args.review)
