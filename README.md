# Exegesis Browser: A Portalized Knowledge System for PKD's Exegesis

This repository contains a deterministic, evidence-backed knowledge portal for Philip K. Dick's *Exegesis*. It converts thousands of pages of visionary journals into a relational, browsable index of figures, themes, and theological constructs.

## 🚀 Live Portal
**[View the Exegesis Browser](https://t3dy.github.io/ExegesisBrowser/)**

## 🛠️ Technology Stack & Pipeline

This project uses a multi-phase analytical pipeline designed for scholarly rigor and evidence-based synthesis. All scripts are found in the `scripts/` directory and are designed to be portable and configurable via CLI arguments.

1. **Deterministic Candidate Discovery** (`exegesis_extractor.py`): Identifies high-confidence terms using frequency mining, phrasal pattern matching, and n-gram analysis.
2. **Canonical Term Resolution** (`exegesis_canonicalizer.py`): Normalizes variant spellings (e.g., *B\u00f6hme* \u2192 *Jakob Boehme*) and resolves aliases (e.g., *BIP* \u2192 *Black Iron Prison*).
3. **Evidence Packet Generation** (`exegesis_evidence_generator.py`): Extracts 8-line context windows for every hit using phrase-aware regex matching, ensuring multi-word terms are correctly captured.
4. **Controlled LLM Enrichment** (`exegesis_llm_enricher.py`): Synthesizes evidence packets into structured dictionary entries, strictly constrained by the extracted text.
5. **Static Portal Build** (`build_portal.py`): Orchestrates the pipeline and generates a responsive web portal in the `docs/` directory.
6. **Sitewide Hyperlinking** (`site_hyperlinker.py`): A post-processor that automatically links dictionary terms across all generated pages.

## 📘 Key Scholarly Findings
- **The Hermetic Cluster**: High-confidence data linkages between **Giordano Bruno**, **Paracelsus**, and **Jakob Boehme** as a primary interpretative lineage for Dick.
- **Structural Metaphysics**: **Plotinus** emerges as the donor of the system's structural geometry, rather than personal initiatory lore.
- **Modern Interlocutors**: **William Burroughs** functions as a contemporary control-group for Dick's information-metaphysics.

For a detailed breakdown, see [findings/key_findings.md](findings/key_findings.md) and [findings/methodology.md](findings/methodology.md).

## 📂 Repository Structure
- `docs/`: The built static site (GitHub Pages root).
- `scripts/`: Implementation scripts for the analytical pipeline.
- `data/raw/`: Source text (not included in public repo, add `exegesis_ordered.txt` here).
- `data/intermediate/`: Processed candidates, canonical lists, and evidence packets.
- `findings/`: Scholarly reports and methodology.

## ⚙️ Running Locally
To rebuild the portal from source:
1. Place your `exegesis_ordered.txt` in `data/raw/`.
2. Run the orchestrator:
   ```bash
   python scripts/build_portal.py
   ```
3. Open `docs/index.html` in your browser.

## 📜 Legal & Scholarly Use
This system is intended for research and scholarly interpretation of Philip K. Dick's late visionary work. All definitions are derived strictly from the textual evidence of the *Exegesis*.
