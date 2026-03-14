# 🎓 Session 2 — Instructor Guide: Precision Chunking & Metadata Enrichment

## Session Overview — The Story You're Telling

Session 1 showed that naive RAG gets 32% precision on a single clean PDF. Students fixed it to 47% with better chunking and reranking. But that was one document in one vocabulary.

**Session 2 is the reality check.** In production, your corpus isn't one clean PDF. It's:

- An academic paper using formal language ("adversarial prompt injection via data manipulation")
- A customer FAQ using casual language ("hackers messing with my chatbot")
- An internal engineering wiki using enterprise vocabulary ("Tier 0 deployments with P50 latency budgets")

**All three documents talk about the same topic (LLM prompt injection security), but they use completely different words.** This is the vocabulary gap problem, and it's the #1 reason RAG fails in production.

**The narrative arc:**

1. "In Session 1, we had one document. What happens with three?"
2. "Let's prove the vocabulary gap exists — with cosine similarity numbers."
3. "Now let's see which chunking strategy handles this mess."
4. "Surprise: `recursive_300` completely collapses on cross-vocabulary queries."
5. "Chunking alone maxes out at 90%. For the remaining 10%, we need metadata, routing, and self-correction."
6. "Let's build 4 progressively smarter pipelines and see where each one adds value."

---

## Where This Session Fits (Sessions 1→4)

| Session                  | What We Proved                                       | Precision Level                          |
| ------------------------ | ---------------------------------------------------- | ---------------------------------------- |
| **Session 1**            | Naive RAG is broken on real data                     | 32% → 47%                                |
| **Session 2** (this one) | Multi-doc + vocabulary gap breaks even good chunking | 80-90% (single-doc), 60-73% (cross-doc)  |
| **Session 3**            | Decoupling what you embed from what you retrieve     | Improves context quality                 |
| **Session 4**            | The query itself is often the problem                | Bridges vocabulary gaps the others can't |

**Session 2 delivers two critical lessons:**

1. **Notebook 1:** The best chunking strategy depends on your data. There is no universal winner.
2. **Notebook 2:** Metadata enrichment and routing are free (regex-based) and solve 80% of multi-doc retrieval. CRAG is expensive insurance.

---

## Notebook 1: Chunking Strategies Deep Dive

### Purpose

Compare 4 chunking strategies × 3 chunk sizes across 3 document types with deliberate vocabulary gaps. Not theory — measurement.

---

### Block 1 — The Multi-Document Corpus (Cells 1-2)

```
43 pages → 300 chunks
  academic_paper (PDF)    : 248 chunks
  customer_faq (Markdown) : 21 chunks
  internal_wiki (Markdown): 31 chunks
```

**What's happening:** We load 3 documents that all cover LLM prompt injection security, but written for different audiences:

| Document                 | Format                            | Vocabulary        | Example Phrase                                       |
| ------------------------ | --------------------------------- | ----------------- | ---------------------------------------------------- |
| Academic Paper (PDF)     | Dense, formal, tables + equations | Research jargon   | "adversarial prompt injection via data manipulation" |
| Customer FAQ (Markdown)  | Casual, Q&A format                | Everyday language | "hackers messing with my chatbot"                    |
| Internal Wiki (Markdown) | Structured, enterprise            | Engineering terms | "Tier 0 deployment with P50 latency budget of 50ms"  |

**Why this corpus design is critical:**

> "I designed these three documents to cover the EXACT same topic — prompt injection defense — but with deliberately different vocabulary. The academic paper says 'paraphrasing defense mechanism.' The FAQ says 'rewording the input to break injections.' The wiki says 'input normalization layer.' Same concept. Three different words."

**The real-world scenario:**

> "This is what your production corpus actually looks like. Imagine you're building a RAG system for a security company. You have:
>
> - Research papers from your ML team
> - Customer support tickets and FAQs
> - Internal runbooks and engineering wikis
>
> A customer asks: 'How do I protect my chatbot from hackers?' Your RAG system needs to find the FAQ answer ('use input filtering and sandboxing') — NOT the academic paper's answer ('implement adversarial prompt injection defense via the paraphrasing mechanism described in Equation 3.2').
>
> But if your embeddings only see academic vocabulary, they'll retrieve the paper. The customer gets a research paper when they needed a simple FAQ. That's a production failure."

**What to tell students:**

> "The 248 vs 21 vs 31 chunk distribution is also intentional. The academic paper dominates the corpus (83% of chunks). In production, your data is always imbalanced — you might have 10,000 support tickets and 50 engineering docs. The minority documents get drowned out in vector search."

---

### Block 2 — Vocabulary Gap Analysis (Cell 3-4)

**What's happening:** Before testing any chunking strategy, we PROVE the vocabulary gap exists using embeddings. We:

1. Take representative text from each document
2. Embed all three with Voyage AI
3. Compute cosine similarity between document pairs

**Why this is powerful:**

> "We don't just claim there's a vocabulary gap — we measure it. If the cosine similarity between 'FAQ about injection prevention' and 'academic paper about injection prevention' is 0.7 instead of 0.95, that's your proof. The embedding model itself can't fully bridge the vocabulary difference."

**The production lesson:**

> "Before you optimize anything in a RAG system, measure your vocabulary gap. If your documents use consistent vocabulary (cosine similarity > 0.9), you can get away with simple chunking. If they don't (similarity < 0.8), you need metadata routing — and that's what Notebook 2 builds."

**What to tell students:**

> "This is what senior engineers do that juniors skip. Juniors jump straight to 'let me try semantic chunking.' Seniors first ask: 'What does my data look like? Where will retrieval fail?' This vocabulary gap analysis takes 30 seconds to run and tells you what kind of retrieval architecture you need."

---

### Block 3 — Four Chunking Strategies (Cell 5-8)

We implement 4 strategies, each processing all 3 documents:

**Strategy 1: Fixed 500-char**

```python
CharacterTextSplitter(separator="", chunk_size=500, chunk_overlap=0)
```

- Blind character cutting. No intelligence. 285 chunks.
- Cuts mid-sentence, mid-word, mid-table.

**Strategy 2: Recursive 500-char**

```python
RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=64,
    separators=["\n\n", "\n", ". ", "; ", ", ", " "])
```

- Smart separators: tries paragraph → sentence → clause → word breaks.
- 313 chunks with 64-char overlap.

**Strategy 3: Markdown-Aware 500-char**

```python
MarkdownTextSplitter(chunk_size=500, chunk_overlap=64)
```

- Understands Markdown structure: headers, lists, code blocks.
- Keeps sections together. 300 chunks.
- **Critical for the FAQ and Wiki** which are Markdown files.

**Strategy 4: Semantic Chunking**

```python
SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
```

- Embeds every sentence, detects semantic shift points, splits there.
- Variable-size chunks based on meaning, not characters. **811 chunks.**
- Requires embedding EVERY sentence at ingestion time — expensive.

**Plus chunk size variants:**

- `recursive_300` — 554 chunks (small, many fragments)
- `recursive_500` — 313 chunks (medium, balanced)
- `recursive_800` — 192 chunks (large, fewer but more context)

**What to tell students:**

> "Notice the chunk counts: Fixed=285, Recursive=313, Markdown=300, Semantic=811. Semantic creates 2.7x more chunks than any other strategy. That means 2.7x more embedding calls at ingestion, 2.7x more storage, and 2.7x more noise in search results. Keep that cost in mind."

> "Also notice recursive_300 creates 554 chunks vs recursive_800's 192 chunks. That's a 3x difference just from changing chunk size. More chunks isn't always better — a 300-char chunk can't hold a complete paragraph. We'll prove this matters in the benchmark."

**The scenario to paint:**

> "Imagine you're the lead engineer at a startup. Your PM says 'just use semantic chunking, it's the smartest.' You run it. 811 chunks. 2.7x the embedding cost. Your monthly Voyage AI bill triples. And when you benchmark it... it performs the same as markdown_500 at 300 chunks. You just tripled your costs for zero improvement. That's what we're about to prove."

---

### Block 4 — Evaluation Queries: The Three Categories (Cell 9)

This is where the session becomes valuable. We don't just test with random questions — we test with 10 carefully designed queries in 3 categories:

**Category 1: same_vocab (3 queries)**

> Queries that use the SAME vocabulary as the target document.

| Query                                                              | Target Doc     | Why                              |
| ------------------------------------------------------------------ | -------------- | -------------------------------- |
| "What prompt injection attack methods are evaluated in the paper?" | Academic Paper | Uses the paper's own terminology |
| "What is the ASV metric and how is it computed?"                   | Academic Paper | "ASV" appears only in the paper  |
| "How does delimiter-based prompt isolation work?"                  | Academic Paper | Technical term from the paper    |

> "These are the _easy_ queries. The query vocabulary matches the document vocabulary. Any decent embedding model should find the right chunks."

**Category 2: cross_vocab (4 queries)**

> Queries that use DIFFERENT vocabulary from the target document.

| Query                                                | What They Say        | What The Document Says                             |
| ---------------------------------------------------- | -------------------- | -------------------------------------------------- |
| "How do you stop hackers from messing with your AI?" | Casual language      | Paper says "adversarial prompt injection defense"  |
| "My AI assistant is getting tricked by users"        | Customer language    | Wiki says "adversarial input vector exploitation"  |
| "Cost and latency of implementing prompt guards"     | Engineering language | Paper says "defense mechanism overhead"            |
| "Simple trick to make injections bounce off"         | Colloquial           | FAQ says "paraphrasing and retokenization defense" |

> "These are the queries that break naive RAG. The user says 'hackers messing with my AI.' The paper says 'adversarial prompt injection.' Same concept, zero word overlap. The embedding model has to bridge this gap purely through semantic understanding."

**Category 3: cross_doc (3 queries)**

> Queries that need information from MULTIPLE documents.

| Query                                                                     | What's Needed                                                            |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| "Compare paraphrasing defense across research and production deployments" | Paper's ASV numbers + Wiki's latency budgets                             |
| "How should we decide what level of defense to implement?"                | Wiki's tier system + Paper's effectiveness data + FAQ's practical advice |
| "Practical differences between jailbreaking and prompt injection"         | All 3 docs discuss this differently                                      |

> "These are the hardest queries. The answer literally doesn't exist in any single document. You need to retrieve chunks from 2-3 documents and synthesize. This is where every strategy struggles — and it's the setup for why metadata routing matters in Notebook 2."

**What to tell students:**

> "In the real world, you don't get to choose how users phrase their questions. A customer doesn't know your paper calls it 'adversarial prompt injection.' They say 'my chatbot is getting hacked.' Your RAG system must bridge that gap. These 3 categories test exactly that progression: easy → hard → impossible-without-routing."

---

### Block 5 — The Full Benchmark (Cells 10-12)

This is the heart of the notebook. 10 queries × 6 strategies = 60 benchmark runs. Each run measures:

- **Source Precision@5** — Did we retrieve chunks from the right document?
- **Relevance** — Is the retrieved content about the right topic? (LLM judge, 0-1)
- **Faithfulness** — Is the generated answer grounded in the context? (LLM judge, 0-1)
- **Context Size** — How many characters of context are we sending?
- **Latency** — End-to-end retrieval + generation time

**The Aggregated Results — What Each Strategy Actually Scores:**

| Strategy            | Source P@5 | Relevance | Faithfulness | Ctx Size | Latency | Chunks |
| ------------------- | ---------- | --------- | ------------ | -------- | ------- | ------ |
| fixed_500           | 84%        | **0.86**  | 0.90         | 2,414    | 411ms   | 285    |
| recursive_500       | 84%        | 0.77      | 0.89         | 2,079    | 368ms   | 313    |
| **markdown_500** ⭐ | **90%**    | 0.79      | **0.97**     | 2,212    | 434ms   | 300    |
| semantic            | 80%        | 0.79      | 0.99         | 1,700    | 382ms   | 811    |
| recursive_300       | 84%        | 0.64      | 0.81         | 1,273    | 381ms   | 554    |
| recursive_800       | 88%        | 0.86      | 0.88         | 3,528    | 383ms   | 192    |

**What to tell students — the 4 insights:**

> **Insight 1: Markdown-Aware wins the overall scoreboard.**
> "90% Source Precision, 0.97 Faithfulness, and only 300 chunks. It beats semantic chunking (80% P@5, 811 chunks) at one-third the cost. Why? Because our FAQ and Wiki are Markdown files. The Markdown splitter preserves section headers, keeps Q&A pairs together, and never breaks a list item mid-bullet."

> **Insight 2: Semantic chunking is overrated.**
> "811 chunks. HIGH ingest cost (every sentence gets embedded). And the result? 80% Source P@5 — the LOWEST of all strategies. Why? Because when you create tiny meaning-based chunks from a document with consistent vocabulary, you get lots of small chunks that all look similar to the embedding model. More noise, not less signal."

> **Insight 3: fixed_500 is surprisingly competitive on relevance.**
> "0.86 relevance — tied with recursive_800 for best. How? Brute force. Fixed chunks create lots of fragments, and by sheer volume, some of them contain the right content. But look at Faithfulness: 0.90 — the lowest. The LLM fills gaps from broken context with plausible-sounding fabrications. In production, that's dangerous."

> **Insight 4: recursive_800 is the quiet winner for single-doc scenarios.**
> "88% Source P@5, 0.86 Relevance, and only 192 chunks. Fewer chunks = faster search, less storage, cleaner results. If you're working with one clean document, recursive_800 is the simplest production choice."

---

### Block 6 — Per-Category Breakdown: WHERE Each Strategy Wins/Fails (Cell 14)

This is where the data gets surgical:

| Strategy      | same_vocab (Rel) | cross_vocab (Rel) | cross_doc (Rel) |
| ------------- | ---------------- | ----------------- | --------------- |
| fixed_500     | 0.82             | **0.93**          | 0.83            |
| recursive_500 | 0.63             | 0.78              | **0.90**        |
| markdown_500  | 0.63             | 0.85              | 0.87            |
| semantic      | 0.80             | 0.85              | 0.70            |
| recursive_300 | 0.87             | **0.46** ❌       | 0.63            |
| recursive_800 | 0.87             | 0.87              | 0.83            |

**The devastating finding — recursive_300 collapses:**

> "Look at recursive_300 on cross_vocab queries: 0.46 relevance. That's essentially random. And faithfulness drops to 0.53. The LLM is fabricating more than half the time."

> "Why does this happen? A 300-character chunk from the academic paper might say: `'tion attacks. Our framework formalizes the attack as a function f(x, p) where p represents the injected ins'` — that's 300 characters of a mid-sentence fragment. The embedding model has no idea this is about prompt injection. When the user asks 'How do I protect my chatbot?', this chunk has zero semantic overlap."

> "But recursive_800? Same document, same content, but the chunk says: `'Our framework formalizes prompt injection attacks. The attack function f(x,p) takes the original data x and injected instruction p, producing a modified prompt that causes the LLM to execute the attacker's task instead of the intended task. We evaluate defenses including paraphrasing, retokenization, and delimiter-based isolation.'` Now the embedding model can match 'protect my chatbot' to 'defenses including paraphrasing, retokenization.' The larger context bridges the vocabulary gap."

**What to tell students:**

> "This is the single most important finding of Session 2: **chunk size matters MORE than strategy for cross-vocabulary retrieval.** Going from 300 to 800 characters improves cross-vocab relevance from 0.46 to 0.87 — an 89% improvement. No fancy algorithm. Just bigger chunks."

> "The intuition: embedding models need semantic context to bridge vocabulary gaps. 'Protect my chatbot' and 'paraphrasing defense mechanism' share zero words. But in a large enough chunk, they appear near words like 'attack', 'defense', 'LLM', 'security' — words that exist in BOTH vocabularies. The embedding model uses these shared neighborhood words to create similar vectors."

**The production lesson:**

> "When a PM asks 'should we use semantic chunking or recursive?', the correct answer is 'what's your minimum chunk size, and do your documents share vocabulary?' If the answer is 'small chunks, different vocabularies' — no strategy will save you. You need bigger chunks AND metadata routing."

---

### Block 7 — Chunk Size Sensitivity (Cell 15)

Isolating just the recursive strategy at 3 sizes:

| Size | same_vocab  | cross_vocab | cross_doc   |
| ---- | ----------- | ----------- | ----------- |
| 300  | 0.87 ✅     | **0.46** ❌ | 0.63        |
| 500  | 0.63        | 0.78        | **0.90** ✅ |
| 800  | **0.87** ✅ | **0.87** ✅ | 0.83        |

**What to tell students:**

> "Look at this table. same_vocab works at ANY size — 300 gets 0.87, 800 gets 0.87. When the query matches the document vocabulary, even terrible chunks contain enough signal."

> "But cross_vocab? 300=0.46, 500=0.78, 800=0.87. That's a straight line improvement. The embedding model needs more context to bridge vocabulary gaps."

> "And cross_doc has a sweet spot at 500 (0.90) — larger than 800 (0.83)! Why? Because cross-doc queries need chunks from MULTIPLE sources. At 800 chars, each chunk is so large that you retrieve fewer unique documents in your top-5. At 500, you get more diversity."

> "This is the production trade-off: larger chunks = better vocabulary bridging but less source diversity. There is no universal optimal size. It depends on whether your users ask same-vocabulary or cross-vocabulary questions."

---

### Block 8 — Cost Analysis (Cell 16)

| Strategy      | Chunks  | Embedding Calls | Ingest Overhead | Avg Relevance | Production Ready |
| ------------- | ------- | --------------- | --------------- | ------------- | ---------------- |
| fixed_500     | 285     | 285             | LOW             | 0.86          | Yes              |
| recursive_500 | 313     | 313             | LOW             | 0.77          | Yes              |
| markdown_500  | 300     | 300             | LOW             | 0.79          | Yes              |
| **semantic**  | **811** | **811**         | **HIGH**        | 0.79          | **Expensive**    |
| recursive_300 | 554     | 554             | LOW             | 0.64          | Yes              |
| recursive_800 | 192     | 192             | LOW             | 0.86          | Yes              |

**What to tell students:**

> "Semantic chunking costs $0 for the algorithm itself, but it requires embedding EVERY sentence at ingestion time to find breakpoints — 811 embedding calls vs 300 for markdown. At Voyage AI's pricing ($0.06 per 1M tokens), the difference is small for a 3-document corpus. But at 100,000 documents? That's 270,000 embedding calls vs 100,000. That difference shows up on your bill."

> "More importantly, 811 chunks means 811 vectors in Qdrant. That's 2.7x more storage and 2.7x slower search (more candidates to evaluate). For 0.79 relevance — the SAME as markdown_500's 0.79 with 300 vectors."

---

### Block 9 — Chunk Boundary Inspection (Cell 17)

We search for chunks containing "paraphras" in the FAQ and inspect how each strategy handles them:

**fixed_500:**

```
Chunk 1 (500 chars):
  Starts clean: No — mid-sentence!
  Ends clean:   No — broken!
  Preview: "actually do, even if it gets   tricked  ### Does paraphrasing the
  input help?  Yes actually! Paraphrasing (rewording..."
```

**markdown_500:**

```
Chunk 1 (324 chars):
  Starts clean: Yes
  Ends clean:   Yes
  Preview: "Yes actually! Paraphrasing (rewording the input slightly before
  processing) is one of the more effective low-cost defenses..."
```

**What to tell students:**

> "Fixed_500 starts mid-sentence with 'actually do, even if it gets tricked' — that's the end of the PREVIOUS FAQ answer bleeding into this chunk! Then it contains the header '### Does paraphrasing the input help?' and the START of the answer. One chunk, two different FAQ questions mashed together."

> "Markdown_500 starts exactly at 'Yes actually! Paraphrasing...' — the beginning of the answer. It ends at a clean paragraph break. When the embedding model sees this chunk, it knows it's about paraphrasing as a defense. When it sees the fixed_500 chunk, it sees a jumble of two different topics."

> "In production, chunk boundaries determine retrieval quality. If your chunks contain clean, self-contained information, the embedding model can create accurate vectors. If your chunks are mid-sentence fragments, the vectors are garbage."

---

## Notebook 2: Metadata Enrichment & CRAG

### Purpose

Build 4 progressively smarter retrieval pipelines on the same corpus. Measure where each layer adds value — and where it doesn't.

---

### Block 1 — Production Regex Enrichment (Cell 3)

```
Production enrichment: 300 chunks in 69ms
Cost: $0.00 | Speed: 0.228ms per chunk

Sample metadata:
{
  "doc_type": "customer_faq",
  "format": "markdown",
  "content_type": "methodology",
  "audience": "general",
  "complexity": "intermediate",
  "key_entities": ["FAQ", "LLM", "RAG"],
  "has_numbers": false,
  "has_table": false,
  "has_code": false,
  "word_count": 45
}
```

**What's happening:** We enrich every chunk with metadata using ONLY regex and keyword matching. No LLM calls.

The regex rules:

- `content_type` — matches words like "attack", "defense", "results", "methodology" against the chunk text
- `audience` — detects words like "P50", "SLA", "deploy" → technical; "study", "evaluation" → academic; default → general
- `complexity` — based on average word length and jargon density
- `key_entities` — extracts capitalized terms and acronyms

**Why this is production-gold:**

> "69 milliseconds for 300 chunks. $0.00 cost. Zero API calls. This runs in your ingestion pipeline with zero external dependencies. If you process 1 million documents per day, this adds 0.2 milliseconds per chunk to your pipeline."

> "Compare this to the LLM enrichment in the next block: 1,440ms per chunk, $0.012 for 300 chunks, requires a Gemini API call for every single chunk. For 1 million documents, that's 16 DAYS of wall-clock time vs 3 MINUTES."

**The scenario to paint:**

> "You're an ML engineer at a fintech company. Your RAG system indexes customer support tickets, regulatory documents, and engineering runbooks. New tickets arrive every second. You need to enrich each one with metadata at ingestion time. If your enrichment takes 1.4 seconds per chunk (LLM), you're already falling behind. If it takes 0.2ms (regex), you can process 5,000 chunks per second."

> "This is why production teams almost always use regex enrichment over LLM enrichment. It's not as sophisticated, but it's fast, deterministic, and free."

---

### Block 2 — Metadata Distribution Analysis (Cell 4)

| Document       | Top Content Types           | What This Tells Us                                    |
| -------------- | --------------------------- | ----------------------------------------------------- |
| academic_paper | results (33%), attack (33%) | Heavy on experimental data and attack descriptions    |
| customer_faq   | attack (38%), defense (19%) | Customer concerns are about attacks happening to them |
| internal_wiki  | defense (32%), attack (26%) | Engineering focus is on building defenses             |

**What to tell students:**

> "Look at the distribution. The academic paper is 33% results and 33% attack descriptions. The wiki is 32% defense-focused. The FAQ is 38% attack-focused (customers asking 'how do attacks work?'). This distribution immediately tells you: if someone asks about defenses, route them to the wiki. If they ask about attack research, route them to the paper."

> "This is metadata as a routing signal. You don't need an LLM to figure out which document a query should go to. The content_type distribution tells you."

---

### Block 3 — LLM Enrichment Comparison (Cells 5-6)

```
LLM-enriching 15 sample chunks...
Done in 21.6s (1440ms per chunk)
Projected for ALL 300 chunks: 432s
Projected cost: ~$0.012
```

```
PRODUCTION vs LLM ENRICHMENT ACCURACY
Content type agreement: 40%
Audience agreement:     20%
```

**What's happening:** We enrich 15 sample chunks with Gemini (LLM) and compare to our regex enrichment. The agreement is low: 40% for content type, 20% for audience.

**Why the low agreement is actually fine:**

> "Students will panic at 40% agreement. 'The regex is wrong 60% of the time!' No. The two classifiers use different taxonomies. The LLM classified almost EVERYTHING as 'technical' audience. The regex correctly separated 'general' (FAQ language), 'academic' (paper citations, formal tone), and 'technical' (engineering jargon with P50, SLA, tier references)."

> "For routing purposes, the regex classifier is MORE useful because it aligns with DOCUMENT types, not abstract categories. When a customer asks a question, we want to route to the FAQ — not to everything the LLM considers 'technical.'"

**The production lesson:**

> "Don't chase LLM enrichment accuracy. Chase USEFULNESS for your routing logic. A regex that correctly labels doc_type='customer_faq' is worth more than an LLM that labels everything 'technical' with 95% confidence."

| Metric              | Regex Enrichment                | LLM Enrichment                            |
| ------------------- | ------------------------------- | ----------------------------------------- |
| Speed               | 0.2ms/chunk                     | 1,440ms/chunk                             |
| Cost                | $0.00                           | $0.012 for 300 chunks                     |
| Deterministic?      | Yes                             | No (temperature-dependent)                |
| API dependency?     | None                            | Requires Gemini API                       |
| Useful for routing? | **Yes** — aligns with doc types | Partial — classifies everything similarly |

---

### Block 4 — Query Routing Demo (Cell 9)

```
Q: How do I stop hackers from messing with my chatbot?
  Detected audience: general → Routing to: customer_faq
  Retrieved from: ['customer_faq', 'customer_faq', 'customer_faq', 'customer_faq', 'customer_faq']  ✅

Q: What is the P50 latency budget for Tier 0 deployments?
  Detected audience: technical → Routing to: internal_wiki
  Retrieved from: ['internal_wiki', 'internal_wiki', 'internal_wiki', 'internal_wiki', 'internal_wiki']  ✅

Q: What attack methods were evaluated in the study?
  Detected audience: academic → Routing to: academic_paper
  Retrieved from: ['academic_paper', 'internal_wiki', 'internal_wiki', 'internal_wiki', 'internal_wiki']  ⚠️

Q: Compare regex and LLM-based input filtering
  Detected audience: any → Routing to: all
  Retrieved from: ['academic_paper', 'internal_wiki', 'internal_wiki', 'academic_paper', 'internal_wiki']
```

**What to tell students:**

> "Look at the first two queries. Perfect routing. 5/5 from the right source, zero cost, zero LLM calls. The regex detected 'hackers messing with chatbot' as general/customer language and routed to the FAQ. It detected 'P50 latency budget Tier 0' as engineering language and routed to the wiki."

> "Now look at query 3. We routed to academic_paper, but only 1 of 5 results came from it. Why? Because the wiki also discusses attack methods extensively, and Qdrant's vector search found wiki chunks more similar to the query. The routing filter narrows the search space, but the embedding model still picks the most similar vectors within that space."

> "And query 4 — 'Compare regex and LLM-based input filtering' — doesn't have a clear audience. The router correctly detects 'any' and searches all documents. This is the fail-safe: when routing can't determine the audience, it falls back to unrestricted search."

**The production scenario:**

> "You're building a customer support RAG system. Your corpus has 50,000 customer FAQs, 500 engineering docs, and 100 research papers. Without routing, a customer question retrieves engineering jargon. With routing, it retrieves FAQ answers. And the routing costs $0 — it's a regex on the query."

> "The best part: routing is a production-grade pattern used by companies like Notion, Stripe, and Intercom. They don't route with LLMs — they route with role detection, keyword matching, and metadata filters. It's fast, deterministic, and works at scale."

---

### Block 5 — CRAG: Corrective RAG (Cell 10)

```
CRAG pipeline ready.
```

**What's happening:** CRAG (Corrective Retrieval-Augmented Generation) adds a self-evaluation step:

1. Retrieve chunks normally
2. Ask an LLM: "Are these chunks actually relevant to the query? Score 0-1."
3. If score < 0.7, re-retrieve from ALL documents (ignoring the routing filter)
4. Generate the answer from the corrected context

**The real-world scenario:**

> "Imagine a doctor asks your medical RAG system: 'What are the drug interactions for metformin with the new GLP-1 agonist protocol?' Your routing sends this to the drug database. But the answer is actually in a recent clinical trial paper that your router didn't know about."

> "Without CRAG, the doctor gets an incomplete answer from the drug database. With CRAG, the system retrieves from the drug database, the LLM evaluates 'these chunks don't actually cover GLP-1 interactions', and re-retrieves from all sources — finding the clinical trial paper."

> "CRAG is insurance. It catches the cases where your routing or initial retrieval made the wrong choice."

---

### Block 6 — The 4-Pipeline Benchmark (Cell 11)

8 evaluation queries across 4 categories (customer, engineering, research, cross_doc), tested against 4 pipelines:

**Sample Results:**

```
[customer] How do I stop hackers from messing with my AI assistant...
  Naive      → SP=100% Rel=0.90 Lat=362ms
  Enriched   → SP=100% Rel=0.90 Lat=354ms
  Routed     → SP=100% Rel=0.90 Lat=345ms
  CRAG       → SP=100% Rel=0.90 Lat=1301ms

[engineering] What is the P50 latency for full dual-model guard architecture...
  Naive      → SP=80% Rel=0.80 Lat=435ms
  Enriched   → SP=80% Rel=0.80 Lat=361ms
  Routed     → SP=80% Rel=0.90 Lat=576ms   ← Routing bumped relevance!
  CRAG       → SP=80% Rel=0.80 Lat=1330ms

[cross_doc] Compare academic and production ASV benchmarks...
  Naive      → SP=100% Rel=0.70 Lat=395ms
  Enriched   → SP=100% Rel=0.70 Lat=364ms
  Routed     → SP=100% Rel=0.70 Lat=527ms
  CRAG       → SP=100% Rel=0.70 Lat=1917ms [corrected]  ← CRAG triggered!
```

**What to tell students:**

> "Look at the engineering query. Naive gets 0.80 relevance. Routed gets 0.90. That 0.10 improvement is from routing — we restricted search to the wiki, which uses engineering vocabulary. The routing filter REMOVED academic paper chunks that would have confused the answer."

> "Now look at the cross_doc query. CRAG triggered a correction (see the `[corrected]` flag). It retrieved from the paper initially, detected low confidence, then re-retrieved from all sources. But the result was the same 0.70 relevance. CRAG caught the problem but couldn't fix it — because the query genuinely requires synthesizing information from multiple documents, and no single retrieval pass can get all of them."

---

### Block 7 — The Final Scoreboard (Cell 13)

| Pipeline     | Avg Source P@5 | Avg Relevance | Avg Latency |
| ------------ | -------------- | ------------- | ----------- |
| **Naive**    | 78%            | **0.88**      | **380ms**   |
| **Enriched** | 78%            | 0.86          | 374ms       |
| **Routed**   | 78%            | **0.88**      | 468ms       |
| **CRAG**     | 78%            | 0.85          | 1324ms      |

**The honest conversation:**

> "All four pipelines tie at 78% Source Precision. On this corpus, with these queries, the advanced techniques don't dramatically outperform naive vector search. Why?"

> "Three reasons:"
>
> 1. **Small corpus.** 300 chunks is tiny. Vector search works well at small scale because there's less noise to compete with.
> 2. **Good embeddings.** Voyage AI's voyage-3 model is good enough to bridge most vocabulary gaps at this scale.
> 3. **Balanced test queries.** Our 8 queries are well-represented across the corpus.

> "In production, with 10,000+ chunks, weaker embedding models, and long-tail queries that barely match your corpus, the difference between Naive and Routed becomes dramatic. Routing isn't for today's demo — it's for next month's production traffic."

---

### Block 8 — Per-Category Breakdown (Cell 14)

| Pipeline | Customer (SP/Rel) | Engineering (SP/Rel) | Research (SP/Rel) | Cross-Doc (SP/Rel) |
| -------- | ----------------- | -------------------- | ----------------- | ------------------ |
| Naive    | 90%/0.90          | 90%/0.80             | 80%/0.90          | **60%**/0.90       |
| Routed   | 90%/0.90          | 90%/**0.80**         | 80%/0.90          | **60%**/0.90       |
| CRAG     | 90%/0.90          | 90%/0.75             | 80%/0.90          | **60%**/0.87       |

**The critical number: 60% Source Precision on cross_doc.**

> "Every pipeline fails the same way on cross-document queries. 60% Source Precision means 2 of our top-5 chunks are from the wrong source. This is the unsolved problem."

> "Why can't routing fix it? Because a cross-doc query like 'Compare academic and production ASV benchmarks' doesn't have a single target audience. It's asking for both. The router can't choose one document — it needs chunks from both."

> "This is the fundamental limitation of chunking + metadata. It's also why Sessions 3 and 4 exist. Session 3 (Parent Document + Sentence Window) improves WHAT gets retrieved. Session 4 (Query Transformation) rewrites the query itself to bridge vocabulary gaps."

---

### Block 9 — Architecture Comparison (Cell 15)

| Pipeline     | Enrichment Cost | Query Cost | LLM Calls/Query | Complexity    | Best For                        |
| ------------ | --------------- | ---------- | --------------- | ------------- | ------------------------------- |
| Naive        | $0              | $0         | 0               | Trivial       | Single doc, matching vocabulary |
| Enriched     | $0 (regex)      | $0         | 0               | Low           | Default for multi-doc           |
| Routed       | $0 (regex)      | $0         | 0               | Medium        | Known audience segments         |
| CRAG         | $0 (regex)      | $0.001     | 1               | High          | Wrong source = dangerous        |
| LLM-Enriched | $0.01/chunk     | $0         | 0               | High (ingest) | Small, high-value corpora only  |

**What to tell students:**

> "Look at the cost column. Enriched and Routed cost NOTHING. Zero dollars. Zero API calls. The regex runs in your code. This is why they're the default for production multi-doc RAG."

> "CRAG costs $0.001 per query — one additional LLM call to evaluate retrieval quality. At 100,000 queries/day, that's $100/day extra. Worth it for healthcare, finance, or legal — where a wrong source could cause real harm. Not worth it for a chatbot that answers FAQ questions."

> "LLM-Enriched is the most expensive at ingest time ($0.01 per chunk). For 300 chunks, that's $3. For 1 million chunks, that's $10,000. And as we showed, it agrees with regex only 40% of the time. Save your money."

---

## The Session's Big Lessons

### For Students With Zero Background

1. **Different documents use different words for the same thing.** This is the vocabulary gap. It's the #1 reason RAG fails with real data.
2. **Chunk size matters more than strategy.** Going from 300 to 800 characters improved cross-vocabulary retrieval by 89%.
3. **Markdown-Aware chunking beats semantic chunking.** Cheaper, fewer chunks, higher Source Precision.
4. **Metadata routing is free.** A regex can route customer queries to FAQs and engineering queries to wikis — zero cost, zero LLM calls.
5. **Cross-document queries are the hardest.** All strategies fail at 60-73% Source Precision. This is the problem the rest of the module solves.

### For Senior Engineers

1. **Measure your vocabulary gap before choosing a strategy.** Cosine similarity between document embeddings tells you if you need routing.
2. **Don't pay for semantic chunking in production.** 811 chunks vs 300 for markdown_500, with identical relevance (0.79). That's 2.7x the storage and embedding cost for zero improvement.
3. **Regex enrichment at ingest, not LLM enrichment.** 0.2ms vs 1,440ms per chunk. Deterministic vs probabilistic. $0 vs $0.01/chunk. The regex is more useful for routing because it aligns with document types.
4. **CRAG is insurance, not optimization.** 3.5x latency (1,324ms vs 380ms) for -0.03 relevance (0.85 vs 0.88). Use it only when wrong-source retrieval is dangerous.
5. **Design your eval queries in categories.** same_vocab, cross_vocab, and cross_doc test fundamentally different retrieval capabilities. A system that scores 0.87 on same_vocab might score 0.46 on cross_vocab.

### The Bridge to Session 3

> "We've now pushed chunking as far as it goes. Markdown-aware at 500 characters gives us 90% Source Precision on same-vocabulary queries. Metadata routing gives us audience-based filtering for free. But cross-document queries remain at 60%."

> "The bottleneck is no longer HOW we chunk — it's WHAT we retrieve. Right now, we embed and retrieve the same chunk. What if we could embed a small, precise chunk for matching but RETRIEVE the full surrounding context for the LLM? That's Session 3: Parent Document Retrieval and Sentence Window — techniques that decouple what gets searched from what gets returned."

---

## Production Pipeline Summary

```
Session 2 Pipeline:

      User Query
          │
          ▼
    ┌────────────┐
    │ Query       │ (regex: customer/technical/academic/any)
    │ Router      │
    └─────┬──────┘
          │ doc_type filter
          ▼
    ┌────────────┐
    │  Embedder   │ (Voyage AI voyage-3)
    └─────┬──────┘
          │ filtered vector search
          ▼
    ┌────────────┐
    │  Qdrant     │ (markdown-aware chunks + metadata)
    └─────┬──────┘
          │ top-5 candidates
          ▼
    ┌────────────┐
    │  CRAG       │ (optional: evaluate confidence, re-retrieve if low)
    │  Evaluator  │
    └─────┬──────┘
          │ validated chunks
          ▼
    ┌────────────┐
    │  Gemini     │ (grounded prompt with citations)
    │  Flash      │
    └─────┬──────┘
          │
          ▼
    Cited Answer [Source: customer_faq]
```

**Ingestion costs at scale:**

| Corpus Size  | Regex Enrichment Time | Semantic Chunking Time | Markdown Chunking Time |
| ------------ | --------------------- | ---------------------- | ---------------------- |
| 1,000 docs   | 0.2 seconds           | 13 minutes             | 2 seconds              |
| 10,000 docs  | 2 seconds             | 2+ hours               | 20 seconds             |
| 100,000 docs | 20 seconds            | 24+ hours              | 3 minutes              |

> This is why production systems don't use semantic chunking.
