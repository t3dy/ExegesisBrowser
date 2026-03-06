# Methodology & Audit Trail

The Exegesis Browser represents a transition from speculative reading to a data-driven, portalized knowledge system. This document outlines the technical and scholarly methodology used to generate the dictionary and portal.

## 1. Deterministic Extraction Pipeline

The core of the system is built on a "deterministic-first" principle. Before any LLM synthesis occurs, the raw text of the *Exegesis* is processed through several Python engines:

### A. Candidate Discovery (`exegesis_extractor.py`)
- **Frequency Mining**: Identifies capitalized terms with high recurrence across 8,000+ pages.
- **Phrasal Pattern Matching**: Uses regex to identify specific theological constructs like "the X of Y" (e.g., "The Ground of Being").
- **Naming Heuristics**: Captures terms immediately following markers like "called," "name," or "persona."
- **N-gram Analysis**: Detects recurring multi-word clusters that indicate technical constructs.

### B. Canonicalization & Alias Resolution (`exegesis_canonicalizer.py`)
- **Variant Normalization**: Merges different spellings and OCR variations (e.g., *B\u00f6hme*, *Bohme*, *Boheme*) into a single canonical entry.
- **Alias Mapping**: Resolves known PKD-specific acronyms (e.g., *BIP* \u2192 *Black Iron Prison*) and personae (e.g., *Thomas* \u2192 *Thomas*).
- **Manual Overrides**: High-importance figures like *Giordano Bruno* and *Paracelsus* are manually anchored to ensure consistency.

### C. Evidence Packet Generation (`exegesis_evidence_generator.py`)
- **Phrasal Matching**: Unlike simple token matching, the system uses regex to find exact phrasal aliases (e.g., "Black Iron Prison") within paragraph blocks.
- **Context Windows**: For every hit, an 8-line context window is extracted to preserve the surrounding logic and tone.
- **Co-occurrence Detection**: Identifies other canonical terms appearing in the same context to build a relational map.

## 2. Controlled LLM Enrichment (`exegesis_llm_enricher.py`)

The LLM is used strictly as a **synthesis engine**, not a knowledge source. 
- **Input Constraints**: The LLM is provided *only* with the pre-extracted evidence packets. 
- **Prompt Engineering**: The model is instructed to distinguish between Dick's views and his citations of historical figures.
- **JSON Output**: The model produces a structured dictionary entry with:
    - Short/Extended Definitions
    - Significance in PKD's System
    - Scholarly Cautions (ambiguities/weak evidence)

## 3. Static Site Export & Deployment (`build_portal.py`)

To ensure durability and accessibility, the system exports a pre-built static site:
- **Card Generation**: Every dictionary entry becomes a standalone HTML "Card" portal.
- **Sitewide Hyperlinking**: A regex-based post-processor scans the final site and hyperlinks all dictionary terms to their respective pages.
- **GitHub Actions**: Automated deployment ensures that any updates to the script or source text are reflected in the live portal.

## 4. Audit Trail & Verification

- **Uncertainty Tracking**: Terms with zero passages or extremely low counts are flagged for manual review in `data/review/`.
- **Transparency**: Every dictionary entry links back to its raw evidence packet, allowing users to verify the synthesis against the original text.
- **Manual Review**: High-level synthesis (e.g., the relationship between Bruno and Burroughs) is subject to human scholarly oversight.
