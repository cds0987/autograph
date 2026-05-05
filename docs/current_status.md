# Current Project Status

## Overview

`autograph` is a Python knowledge-graph builder that turns structured records into:

- in-memory graph nodes and relationships
- optional semantic-search vectors
- Neo4j graph data written through generated Cypher

The current codebase supports JSON, JSONL, CSV, and other structured record inputs through the loader/detector flow. It can enrich records with heuristic extraction and optional LLM extraction, then publish the resulting graph into Neo4j.

Distribution and import names are intentionally different:

- PyPI distribution: `autograph-llmneo4j`
- Python import: `autograph`

## Current Flow

The end-to-end pipeline currently works like this:

1. Load records with `GraphBuilder.load_data(...)`
2. Infer schema with `SchemaAnalyzer`
3. Extract entities with `EntityExtractor`
4. Build nodes and relationships with `RelationshipBuilder`
5. Optionally generate embeddings for semantic search
6. Export Cypher and push the graph to Neo4j

The public entrypoint is exposed from [__init__.py](/abs/path/d:/Training/graphdatabase/autograph/__init__.py:1) as:

- `GraphBuilder`
- `GraphConfig`

## Working Features

- Structured data loading from file-based sources
- Automatic graph construction from records
- LLM-assisted entity extraction using configured provider settings
- Heuristic fallback extraction when LLM output is unavailable or incomplete
- Semantic search through embeddings and a vector index
- Neo4j export and database reset/write flow
- Integration tests that exercise live fetch -> build -> Neo4j verification

## Current Test Coverage

The most complete live integration test is [tests/test_final_json.py](/abs/path/d:/Training/graphdatabase/autograph/tests/test_final_json.py:1).

It currently does the following:

1. Fetches a configurable number of AI news articles using [tests/fetch_ai_articles.py](/abs/path/d:/Training/graphdatabase/autograph/tests/fetch_ai_articles.py:1)
2. Writes fetched data to temporary JSON/JSONL/CSV outputs
3. Loads the fetched JSON into `GraphBuilder`
4. Builds the graph with:
   - `gpt-4o-mini` for extraction
   - `text-embedding-3-small` for embeddings
5. Pushes the graph into Neo4j
6. Verifies:
   - fetched record count
   - node labels
   - relationship types
   - semantic search returns results
   - Neo4j node and relationship counts match expectations

The fetch size is controlled with:

```powershell
$env:AI_ARTICLES_LIMIT="3"
```

Dev-style readable logs are enabled with:

```powershell
$env:SUP_ENV="dev"
```

## Recent Improvements

### 1. Flexible live-data integration test

`tests/test_final_json.py` was rewritten to:

- fetch fresh AI article data dynamically
- avoid relying on a single fixed checked-in JSON dataset
- scale assertions with however many articles were fetched

### 2. Better per-record extraction logging

[core/graph_builder.py](/abs/path/d:/Training/graphdatabase/autograph/core/graph_builder.py:89) now logs richer per-record details during graph construction:

- `build.entity_extraction.record`
- `build.entity_extraction.entities`
- `build.entity_extraction.record_done`

These logs now show:

- extracted bucket counts per record
- sentiment
- built node counts by label
- built relationship counts by type
- how many nodes/relationships were actually added after deduplication
- cumulative graph totals after each record

This makes it much easier to understand what each LLM-assisted extraction step contributed.

## Example Observed Result

A successful run with `AI_ARTICLES_LIMIT=1` produced:

- `1` fetched article
- `20` final graph nodes
- `22` final graph relationships
- `7` `Entity` nodes
- `11` `Topic` nodes
- `1` `Source` node
- `1` `Record` node

The same run also showed:

- `15` `MENTIONS` relationships
- `5` `HAS_KEYWORD` relationships
- `1` `PUBLISHED_BY` relationship
- `1` `TAGGED_WITH` relationship

## Known Issues And Gaps

### Packaging still needs a live publish verification

The package metadata has been updated for PyPI distribution name `autograph-llmneo4j`, while keeping the Python import path as `autograph`.

The repository also includes GitHub Actions for CI and PyPI publishing, but the final verification step depends on successful trusted publishing and a live PyPI release.

### Environment sensitivity

Some test runs can fail because of local temp-folder or cache permissions on Windows, even when the code itself is correct. This affected pytest temp directory creation in one observed run.

### Warning noise

Live Neo4j runs currently emit many Python 3.14 deprecation warnings from the Neo4j driver around `asyncio.iscoroutinefunction`.

## Suggested Next Steps

1. Verify the first successful PyPI publish for `autograph-llmneo4j`
2. Add a workspace-local temporary output strategy for tests if temp-dir flakiness continues
3. Optionally log LLM-only vs heuristic-only extraction contributions separately
4. Add installation examples to the main docs after the first public release
