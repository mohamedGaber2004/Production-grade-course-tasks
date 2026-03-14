# Session 2: Precision Chunking & Metadata Enrichment

## 📖 Session Overview

This session breaks down how to move beyond arbitrary, fixed-size chunks to intelligent **Semantic Chunking** and **Recursive Character Splitting**. We also dive deeply into **Metadata Enrichment**, teaching you how to implement metadata strategies to ensure source traceability, filtering, and document self-correction during the ingestion phase.

---

## 🧩 Chunking Strategies: Recursive vs Semantic

### 1. Recursive Character Splitting

**How it works**: Recursively breaks down text into smaller chunks using a predefined hierarchy of separators (e.g., double newlines, single newlines, spaces, individual characters) until the chunk size constraint is met.

- **Strengths**:
  - Balances context preservation with simplicity.
  - Less computationally intensive than semantic chunking.
  - An excellent default baseline for most applications.
- **Limitations**:
  - Relies on structural rules (newlines/spaces) rather than the actual meaning of the text.
  - Can still split related thoughts if they span across a hard physical boundary.

### 2. Semantic Chunking

**How it works**: Divides text into meaningful segments based on the actual content and relationships between phrases. It uses NLP embeddings to group sentences with high similarity scores into cohesive units.

- **Strengths**:
  - High context preservation; every chunk is semantically cohesive.
  - Reduces redundancy across chunks.
  - Significantly improves retrieval precision for complex queries.
- **Limitations**:
  - High computational cost (requires generating embeddings for every sentence during the ingestion pipeline).
  - Can be overkill for highly structured, simple documents (e.g., CSV databases).

---

## 🏷️ Metadata Enrichment Strategies

Adding descriptive information to document chunks is vital for advanced retrieval.

- **Attribute-based Filtering**: Tag documents with metadata (e.g., `date`, `author`, `topic`, `clearance_level`). Allows pre-retrieval filtering in the Vector DB to narrow the search space drastically.
- **Automated Extraction**: Use LLMs during the document ingestion pipeline to extract implicit metadata (e.g., identifying the "Summary" of a report) and append it as structured data.
- **Pre-Chunking Enrichment**: _Best Practice:_ Always append document-level metadata to the text _before_ chunking, ensuring every resulting chunk natively carries the contextual information of the parent document.

---

## 🔎 Source Traceability & Document Self-Correction

### Source Traceability

Building trust in an Enterprise AI system requires tracking the origin of generated information.

- **Verifiable Citations**: RAG outputs must provide clear, actionable links or citations pointing users to the exact snippet of the source document used to generate the answer.
- **Metadata Storage**: Store variables like `source_url`, `page_number`, and `document_id` inside the vector payload to allow the UI to render proper attributions.

### Document Self-Correction

Self-correction allows a RAG system to evaluate its own retrieval and detect errors before responding dynamically.

- **Feedback Loops**: Utilize implicit signals (user thumbs up/down) to adjust future retrieval weights.
- **Corrective Retrieval-Augmented Generation (CRAG)**: A systematic flow where a lightweight evaluator scores retrieved documents (Correct, Incorrect, Ambiguous). If "Incorrect," the system triggers a fallback action, such as a web search or abandoning the query, rather than hallucinating an answer.
- **Agentic RAG**: An agent uses "reflection" to review its own generated work and iterativley improves the response by adjusting the retrieval query on the fly.
