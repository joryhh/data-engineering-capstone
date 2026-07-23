Student: Jory Alhassan

Program: SDAIA Academy — Modern Data Engineering for AI Systems

Session dates: 19 July 2026 – 23 July 2026

Trainer: Mohammed Albeladi

# Wafra — Data Engineering Capstone

This is my capstone project for the **Modern Data Engineering for AI Systems**
track at **SDAIA Academy** (Learning Space).

## What this is

I built a small end-to-end pipeline around a fictional Saudi retailer called
"Wafra," touching every stage a real data platform needs: getting data in
safely, storing it properly, turning it into something useful, answering
questions about it with AI, and making sure the whole thing runs on its own
and doesn't silently break.

Concretely, that means: a Kafka pipeline that rejects bad records before they
even get in, a Delta Lake with proper Bronze/Silver/Gold layers and a real
MERGE (not a fake upsert), a RAG system that actually combines keyword and
semantic search instead of picking one, an Airflow DAG that stops the
pipeline if data quality checks fail, and OpenLineage tracking so you can see
what ran and what didn't.

## Pipeline Architecture

```
Kafka Producer (Pydantic-validated) ──▶ Kafka Topic ──▶ Kafka Consumer
                                                              │
                                                              ▼
                                    Bronze (raw) ──▶ Silver (MERGE/upsert)
                                                              │
                                                              ▼
                                              Great Expectations Quality Gate
                                                              │
                                              (gate must pass, or Airflow halts)
                                                              │
                                                    Gold (aggregated KPIs)

Airflow DAG wires: bronze_layer >> silver_layer >> quality_gate >> gold_layer

Separately: RAG pipeline (chunking → ChromaDB + BM25 hybrid search with RRF
→ cross-encoder rerank → Groq LLM grounded answer with citations) answers
customer-support questions from a small knowledge base.
```

## How it's organized

```
data-engineering-capstone/
├── ingestion/          # Kafka producer + consumer, Pydantic validation, quarantine log
├── lakehouse/          # Bronze -> Silver -> Gold with Delta Lake, schema-enforcement proof
├── rag/                # Chunking, ChromaDB + BM25 hybrid search, reranking, LLM answer
├── orchestration/      # Airflow DAG + Docker setup
├── quality_lineage/    # Great Expectations gate + OpenLineage events
└── docs/               # Extra notes on how the pieces fit together
```

## Running it

You'll need Docker Desktop, Python 3.11, Java 17 (PySpark needs it), and a
free API key from Groq (https://console.groq.com) for the RAG part.

Setup:

    git clone https://github.com/joryhh/data-engineering-capstone.git
    cd data-engineering-capstone
    python3.11 -m venv venv
    source venv/bin/activate
    pip install kafka-python pydantic pyspark==3.5.0 delta-spark==3.2.0 chromadb sentence-transformers rank-bm25 groq python-dotenv great_expectations openlineage-python
    echo "GROQ_API_KEY=your_key_here" > .env

Ingestion:

    cd ingestion && docker compose up -d && cd ..
    python ingestion/producer.py
    python ingestion/consumer.py

Lakehouse:

    python lakehouse/bronze_layer.py
    python lakehouse/silver_layer.py
    python lakehouse/gold_layer.py
    python lakehouse/prove_schema_enforcement.py

RAG:

    python rag/vector_store.py
    python rag/generate_answer.py

Quality + Lineage:

    python quality_lineage/quality_gate.py
    python quality_lineage/prove_gate_failure.py
    python quality_lineage/lineage_tracker.py

The whole thing via Airflow:

    cd orchestration
    docker compose up -d --build

Then go to localhost:8080, log in as admin (password is generated on
first run — check with `docker exec capstone-airflow cat /opt/airflow/standalone_admin_password.txt`),
and trigger `wafra_capstone_pipeline`. If `quality_gate` fails, `gold_layer`
won't run — that's intentional.

## Sample Results

**Ingestion:** 2 out of 5 sample orders accepted and sent to Kafka; 3 rejected
and written to `quarantine.jsonl` with reasons (empty product, negative price,
negative quantity).

**Lakehouse:** Bronze lands 4 raw rows. Silver's MERGE updates one existing
order (quantity 1 → 3) and inserts one new order, ending at 5 rows total — no
duplicates. Gold produces one aggregated row per product (revenue, units
sold, order count, avg price). The schema-enforcement script ends with Delta
explicitly rejecting a mismatched write.

**RAG:** A question like "How do I get a refund on my Mada card?" returns a
grounded answer citing the exact source chunk, e.g.:
> Refunds to Mada cards may take up to 10 business days to appear.
> [Source: doc4.txt_chunk1]

**Quality Gate:** 5/5 checks pass on clean Silver data. The failure-proof
script deliberately feeds bad data (duplicate ID, negative price, null
product) and shows 3 of the 5 checks correctly failing.

**Lineage:** START/COMPLETE events for a successful stage, and START/FAIL
events for a stage that raises an exception — both printed to the console.

**Airflow:** Triggering `wafra_capstone_pipeline` runs all 4 tasks
(`bronze_layer → silver_layer → quality_gate → gold_layer`) to `success` in
sequence. If `quality_gate` fails, `gold_layer` is never scheduled.

## A note on one design choice

I put the quality gate before Gold instead of after everything, on purpose —
the rubric asks for a gate that actually stops the pipeline, and the most
convincing way to prove that was to make a real downstream stage depend on
it passing.

## Credit

Built as part of SDAIA Academy (https://github.com/SDAIAAcademy)'s Modern
Data Engineering for AI Systems program.
