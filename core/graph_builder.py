"""Main GraphBuilder implementation."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import structlog

from ..analyzers.entity_extractor import EntityExtractor
from ..analyzers.relationship_builder import RelationshipBuilder
from ..analyzers.schema_analyzer import SchemaAnalyzer
from ..embeddings.embedding_generator import EmbeddingGenerator
from ..embeddings.vector_index import VectorIndex
from ..loaders.auto_detector import AutoDetector
from ..graph_store.connection import Neo4jConnection
from ..graph_store.query_builder import QueryBuilder
from ..graph_store.schema_manager import SchemaManager
from ..utils.validators import sanitize_record
from .config import GraphConfig


class GraphBuilder:
    """Turn flexible structured data into a graph model."""

    def __init__(
        self,
        llm_api_key: str | None = None,
        neo4j_uri: str | None = None,
        neo4j_password: str | None = None,
        reset_database: bool = True,
        use_embeddings: bool = False,
        llm_provider: str = "openai",
        verbose: bool = False,
        config: GraphConfig | None = None,
        **overrides: Any,
    ) -> None:
        self.config = config or GraphConfig(
            llm_api_key=llm_api_key,
            llm_provider=llm_provider,
            neo4j_uri=neo4j_uri,
            neo4j_password=neo4j_password,
            reset_database=reset_database,
            use_embeddings=use_embeddings,
            verbose=verbose,
            **overrides,
        )
        self.detector = AutoDetector()
        self.schema_analyzer = SchemaAnalyzer(self.config)
        self.entity_extractor = EntityExtractor(self.config)
        self.relationship_builder = RelationshipBuilder()
        self.embedding_generator = EmbeddingGenerator(self.config)
        self.vector_index = VectorIndex(self.embedding_generator)
        self.schema_manager = SchemaManager()
        self.query_builder = QueryBuilder()
        self.neo4j_connection = Neo4jConnection(self.config)

        self.records: list[dict[str, Any]] = []
        self.schema: dict[str, Any] = {}
        self.graph: dict[str, list[dict[str, Any]]] = {"nodes": [], "relationships": []}
        self._node_index: dict[str, dict[str, Any]] = {}
        self._relationship_index: set[tuple[str, str, str]] = set()
        self._log = structlog.get_logger(component="GraphBuilder")

    def load_data(self, source: Any) -> "GraphBuilder":
        self._log.info("load.start", source=str(source))
        raw_records = self.detector.load(source)
        self.records = [sanitize_record(record) for record in raw_records]
        self._log.info("load.done", records=len(self.records))
        return self

    def build_graph(self) -> dict[str, list[dict[str, Any]]]:
        self._ensure_records_loaded()
        self._log.info("build.start", records=len(self.records), use_llm=self.config.use_llm, use_embeddings=self.config.use_embeddings)

        self._log.info("build.schema_analysis.start")
        self.schema = self.schema_analyzer.analyze(self.records)
        self._log.info("build.schema_analysis.done", primary_label=self.schema["primary_label"], id_field=self.schema["primary_id_field"])

        labels = {
            "primary": self.schema["primary_label"],
            "source": self.config.source_label,
            "entity": self.config.entity_label,
            "topic": self.config.query_label,
        }

        self._log.info("build.entity_extraction.start", total_records=len(self.records))
        for i, record in enumerate(self.records):
            record_ref = record.get("id") or record.get("title", "")[:40]
            self._log.info(
                "build.entity_extraction.record",
                index=i + 1,
                total=len(self.records),
                record_id=record_ref,
            )
            entities = self.entity_extractor.extract(record, self.schema)
            self._log.info(
                "build.entity_extraction.entities",
                index=i + 1,
                total=len(self.records),
                record_id=record_ref,
                entity_counts=self._entity_counts(entities),
                sentiment=entities.get("sentiment"),
            )
            built = self.relationship_builder.build(record, self.schema, entities, labels)
            built_node_counts = self._count_items_by_key(built["nodes"], "label")
            built_relationship_counts = self._count_items_by_key(built["relationships"], "type")
            added_nodes, added_relationships = self._merge_graph_parts(built)
            self._log.info(
                "build.entity_extraction.record_done",
                index=i + 1,
                total=len(self.records),
                record_id=record_ref,
                built_nodes=len(built["nodes"]),
                built_relationships=len(built["relationships"]),
                built_node_labels=built_node_counts,
                built_relationship_types=built_relationship_counts,
                added_nodes=added_nodes,
                added_relationships=added_relationships,
                graph_nodes=len(self.graph["nodes"]),
                graph_relationships=len(self.graph["relationships"]),
            )
        self._log.info("build.entity_extraction.done", nodes=len(self.graph["nodes"]), relationships=len(self.graph["relationships"]))

        if self.config.use_embeddings:
            self._log.info("build.embeddings.start", provider=self.config.embedding_provider, model=self.config.embedding_model)
            texts = [self._record_text(record) for record in self.records]
            self.embedding_generator.prepare(texts)
            for record, text in zip(self.records, texts):
                self.vector_index.add(self._record_id(record), text, record)
            self._log.info("build.embeddings.done", vectors=len(self.records))

        self._log.info("build.done", nodes=len(self.graph["nodes"]), relationships=len(self.graph["relationships"]))
        return self.graph

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if self.config.use_embeddings and self.graph["nodes"]:
            return self.vector_index.search(query, limit=limit)

        query_terms = set(term.lower() for term in query.split())
        scored = []
        for node in self.graph["nodes"]:
            if node["label"] != self.schema.get("primary_label", self.config.article_label):
                continue
            haystack = json.dumps(node["properties"], ensure_ascii=False).lower()
            score = sum(term in haystack for term in query_terms)
            if score:
                scored.append({"id": node["id"], "score": score, "payload": node["properties"]})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]

    def export_json(self, path: str | Path) -> Path:
        target = Path(path)
        target.write_text(json.dumps(self.graph, indent=2, ensure_ascii=True), encoding="utf-8")
        return target

    def export_cypher(self, path: str | Path | None = None) -> str:
        labels = [node["label"] for node in self.graph["nodes"]]
        statements = self.schema_manager.build_constraints(labels)
        statements.extend(self.query_builder.node_merge(node) for node in self.graph["nodes"])
        statements.extend(
            self.query_builder.relationship_merge(rel) for rel in self.graph["relationships"]
        )
        cypher = ";\n".join(statements) + ";"
        if path is not None:
            Path(path).write_text(cypher, encoding="utf-8")
        return cypher

    def push_to_neo4j(self, reset_database: bool | None = None) -> None:
        self._log.info("push.start", uri=self.config.neo4j_uri)
        driver = self.neo4j_connection.create_driver()
        statements = self.export_cypher().split(";\n")
        with driver.session() as session:
            should_reset = (
                self.config.reset_database if reset_database is None else reset_database
            )
            if should_reset:
                self._log.info("push.reset_database")
                self.neo4j_connection.reset_database(session)
            self._log.info("push.write.start", statements=len(statements))
            written = 0
            for statement in statements:
                statement = statement.strip().rstrip(";")
                if statement:
                    session.run(statement)
                    written += 1
            self._log.info("push.write.done", written=written)
        driver.close()
        self._log.info("push.done")

    def get_schema(self) -> dict[str, Any]:
        return self.schema

    def graph_summary(self) -> dict[str, Any]:
        node_counts = defaultdict(int)
        rel_counts = defaultdict(int)
        for node in self.graph["nodes"]:
            node_counts[node["label"]] += 1
        for relationship in self.graph["relationships"]:
            rel_counts[relationship["type"]] += 1
        return {
            "records": len(self.records),
            "nodes": len(self.graph["nodes"]),
            "relationships": len(self.graph["relationships"]),
            "node_labels": dict(sorted(node_counts.items())),
            "relationship_types": dict(sorted(rel_counts.items())),
        }

    def _merge_graph_parts(self, built: dict[str, list[dict[str, Any]]]) -> tuple[int, int]:
        added_nodes = 0
        for node in built["nodes"]:
            existing = self._node_index.get(node["id"])
            if existing is None:
                self._node_index[node["id"]] = node
                self.graph["nodes"].append(node)
                added_nodes += 1
            else:
                existing["properties"].update(node["properties"])
        added_relationships = 0
        for relationship in built["relationships"]:
            key = (relationship["type"], relationship["from"], relationship["to"])
            if key not in self._relationship_index:
                self._relationship_index.add(key)
                self.graph["relationships"].append(relationship)
                added_relationships += 1
        return added_nodes, added_relationships

    def _record_text(self, record: dict[str, Any]) -> str:
        text_fields = self.schema.get("text_fields", [])
        values = [str(record.get(field, "")) for field in text_fields]
        if not any(values):
            values = [str(value) for value in record.values() if isinstance(value, str)]
        return " ".join(value for value in values if value)

    def _record_id(self, record: dict[str, Any]) -> str:
        field = self.schema.get("primary_id_field")
        value = record.get(field) if field else None
        if value:
            return f"{self.schema.get('primary_label', 'Record')}:{value}"
        return f"{self.schema.get('primary_label', 'Record')}:{hash(repr(sorted(record.items())))}"

    def _ensure_records_loaded(self) -> None:
        if not self.records:
            raise ValueError("No records loaded. Call load_data(...) before build_graph().")

    @staticmethod
    def _count_items_by_key(items: list[dict[str, Any]], key: str) -> dict[str, int]:
        counts: defaultdict[str, int] = defaultdict(int)
        for item in items:
            value = item.get(key)
            if value:
                counts[str(value)] += 1
        return dict(sorted(counts.items()))

    @staticmethod
    def _entity_counts(entities: dict[str, Any]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for bucket, value in entities.items():
            if bucket == "sentiment":
                continue
            if isinstance(value, list):
                counts[bucket] = len(value)
        return dict(sorted(counts.items()))
