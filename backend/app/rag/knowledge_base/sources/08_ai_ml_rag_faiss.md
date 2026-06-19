# FinLit AI Stack: ML, RAG, and FAISS

## Purpose

This document explains how FinLit combines deterministic finance logic with AI techniques.

High-level pipeline:
1. profile + feature data
2. simulation/analytics layer
3. retrieval layer (RAG with FAISS)
4. response generation

## Deterministic Core vs AI Layer

FinLit intentionally separates:
- **Deterministic logic** for core financial calculations (spending, stress simulation)
- **AI-assisted generation** for conversational and explanatory outputs

Why this matters:
- deterministic outputs are reproducible and auditable
- AI outputs are contextual and user-friendly but can be probabilistic

## ML in Job-Loss Stress Testing

In job-loss simulations, FinLit can use an ML model to estimate a realistic `cutback_percent` when the user does not explicitly provide one.

Typical feature families:
- needs ratio vs income
- wants ratio vs income
- debt ratio vs income
- user context (dependents, employment status, literacy settings)

Fallback behavior:
- if model unavailable, deterministic rule-based defaults are used
- this ensures continuity and avoids hard dependency on model availability

## RAG (Retrieval-Augmented Generation)

RAG means FinLit retrieves relevant text snippets before generating chat/advice responses.

Benefits:
- better grounding in curated financial content
- reduced hallucination risk vs pure free-form generation
- more consistent domain language

## FAISS Index Role

FAISS stores vector embeddings of documentation chunks.

Typical retrieval process:
1. Convert user query to embedding vector
2. Find nearest chunks in FAISS index
3. Pass those chunks as context to generation model

This supports semantic search: meaning-based retrieval, not only keyword matching.

## Knowledge Chunking Considerations

Chunking strategy impacts retrieval quality:
- chunks that are too short lose context
- chunks that are too long mix topics and reduce precision

Good practice:
- keep chunks focused by topic
- include clear section headings
- avoid duplicated contradictory statements across documents

## Practical Guardrails

Use these safeguards in production-like settings:
- always include confidence and source references in outputs
- separate educational output from regulated advice claims
- prefer explicit assumptions and formulas in scenario explanations
- log and monitor drift between deterministic signals and generated narratives

## Limitations to Communicate Clearly

- AI outputs may still contain errors.
- RAG quality depends on documentation quality and freshness.
- FAISS retrieval similarity does not guarantee perfect factual relevance.
- Stress test scenarios are model assumptions, not guarantees.

## Recommended Team Practices

1. Treat documentation as a first-class model input.
2. Version the knowledge base and rebuild index after meaningful edits.
3. Add scenario interpretation docs whenever scoring logic changes.
4. Keep legal/disclaimer language aligned with product behavior.
