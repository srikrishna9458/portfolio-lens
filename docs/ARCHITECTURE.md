# Architecture and design decisions

These are the rationale and limitations of the implemented design. Alternatives were not benchmarked, so the choices should not be presented as universal performance wins.

## 1. Data grain and provenance

A product row represents a family/platform variant. ThinkPad T14 Gen 6 Arrow Lake and Lunar Lake are separate rows because their memory capabilities differ. A single family-level row would hide this distinction. A purchasable SKU would be a better grain for exact price/value comparisons, but the current research does not consistently establish complete SKUs.

The database contains seven ordinary tables:

| Table | Purpose |
| --- | --- |
| `products` | Platform capabilities and configuration notes |
| `sources` | Manufacturer URLs, summaries and research dates |
| `product_sources` | Many-to-many links between products and evidence |
| `prices` | Dated, sourced observations with market, currency and configuration |
| `launches` | Recorded historical announcements |
| `source_checks` | Retrieval outcomes and page fingerprints |
| `changes` | Audited changes to reviewed product fields |

There is also an FTS5 virtual table and two analytical views. Power BI imports seven tables of its own, including a derived Brands export; these are not identical to the seven ordinary SQLite tables.

Foreign keys prevent invalid source/product references. Check constraints reject impossible numeric values. Imports run in a transaction: a failed batch rolls back its edits and audit entries. Existing source IDs cannot be overwritten; revised evidence requires a new ID. None of these controls proves a researched claim is true—the research still needs review.

## 2. Screening and missing data

`evaluate()` in `app.py` checks explicit thresholds, with this precedence:

1. Any known failed requirement means excluded.
2. Otherwise, any unknown required value means unresolved.
3. Otherwise, the platform is a candidate requiring SKU verification.

A 32 GB memory maximum fails a 64 GB requirement even if upgradeability is unknown. Dell's unverified weight is not evidence that it is heavy, so it remains unresolved when its other requirements pass.

SQL example queries, Python logic, browser interactions and Power BI calculated columns implement related screening rules. Keeping several implementations consistent is a maintenance cost. The tests cover the Python logic; they do not automatically execute and compare every JavaScript and DAX result. A stronger version would introduce shared fixtures and cross-layer checks or centralise the rule calculations.

## 3. Evidence retrieval and generation

`retrieve()` tokenises the question, removes common words, adds a few aliases, and uses SQLite FTS5 with BM25 ranking to return up to six evidence records. It searches curated summaries and linked product names. It does not parse and embed full PDFs at query time.

`answer()` first builds an evidence-supported answer. Recognised portfolio, pricing, portability and market-change questions return deterministic analysis even when local AI is selected. Other questions may send retrieved evidence and instructions to the local model. Recognised routing is keyword-based and can miss or misclassify unusual phrasing.

The llama.cpp path requests structured JSON containing an answer and source IDs. The application checks that the IDs belong to the available evidence; invalid generated citations trigger the existing evidence answer. A valid ID is not proof of factual entailment. The interface displays evidence available for verification, which may be broader than the specific citations in an answer.

This is retrieval-augmented generation without embeddings. The model is pretrained; it was not trained on these laptop records. Local processing avoids a paid cloud-model call for this workflow, but the small model has limited reasoning quality and still consumes local memory and CPU.

## 4. Choices and alternatives

| Implemented choice | Why it fits this version | Alternative and when it would help |
| --- | --- | --- |
| SQLite | A local, portable SQL database with no separate database service | PostgreSQL for a shared service with more concurrent writers and central management |
| Relational tables | Explicit links, repeatable joins, constraints and transaction rollback | A spreadsheet for manual research; it would not by itself provide this application workflow |
| Python standard library | Small dependency footprint for a local HTTP API, SQLite and exports | FastAPI or Django for a larger API, validation conventions, authentication and application structure |
| Plain HTML/CSS/JavaScript | Six local dashboard views without a frontend build pipeline | React or another component framework if UI state, reuse and collaboration become more complex |
| FTS5/BM25 | Simple, inspectable retrieval for a small corpus and exact product names | Semantic or hybrid retrieval if an evaluated question set reveals missed paraphrases |
| Pretrained local Qwen model | An optional model that can run on the laptop | A larger local model or a hosted API after assessing quality, latency, cost and data-handling requirements |
| Deterministic analytical rules | Reproducible numeric screening and explicit treatment of missing values | An LLM can explain evidence, but should not silently redefine numerical requirements |
| Power BI through CSV exports | A transparent bridge from SQLite into a familiar reporting tool | A managed database connection and scheduled refresh for a shared analytics service |
| Reviewed facts plus page checks | Evidence remains traceable and detected changes require interpretation | Automated extraction at scale, with field validation, monitoring and a review queue |
| Local application | Straightforward personal use and demonstration | Hosted deployment after implementing identity, operational controls and production testing |

SQLite supports many readers but one writer at a time per database file; the need for a separate database depends on workload and operating requirements, not merely row count. See [SQLite's deployment guidance](https://www.sqlite.org/whentouse.html). FTS5 supplies the text search and ranking functions used here; see [the FTS5 reference](https://www.sqlite.org/fts5.html).

Python's standard-library HTTP server is not recommended for production use. That is a concrete reason this application should stay local until its serving architecture is replaced and reviewed. See [the Python documentation](https://docs.python.org/3/library/http.server.html).

## 5. Source changes and pricing

A source check fetches an allowed manufacturer's page, checks its robots policy where retrievable, and computes a SHA-256 fingerprint. The first successful result is a baseline. Different bytes on a later fetch mean the page needs review. Marketing text, regional content or dynamic markup can change without a product specification changing.

Only a reviewed research import updates structured product facts and records changed fields. Source checks are user-triggered; there is no autonomous market-wide crawler or recurring scheduler.

Prices carry date, currency, market, kind, tax basis, configuration and source. The seed's USD 999 M4 MacBook Air record is a March 2025 US launch observation for a base configuration. It is not a current quote or the price of a maximum-memory configuration. A value ranking needs comparable offers that this seed does not contain.

## 6. Reporting and verification

Power Query loads the seven CSV exports, promotes headers, converts empty cells to null and assigns data types. DAX provides seven measures and calculated fit columns. Imported CSVs are snapshots: the user must export new research and then refresh the report.

The 78% overview value is average coverage of seven selected specification fields across the sample, rounded for display. It is not model accuracy, research certainty or market coverage.

Seventeen automated tests verify specific behaviours, including rollback, immutable source IDs and the known-failure/missing-value distinction. They do not establish high-load capacity, full browser correctness, complete vulnerability coverage or a quantified model-accuracy score. See `VALIDATION.md` for what was actually exercised.

## 7. Future work, not completed features

Possible extensions include SKU-level offers, a larger evaluated evidence corpus, extraction review queues, database migrations, user accounts, organisation permissions, deployed monitoring and backup restoration tests. The proposed SaaS procurement platform is a separate, unstarted idea; it is not part of this laptop repository.
