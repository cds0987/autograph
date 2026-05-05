"""Optional Neo4j connection manager."""

from __future__ import annotations

from typing import Any

from ..core.config import GraphConfig
from ..core.exceptions import ConfigurationError, IntegrationUnavailableError


class Neo4jConnection:
    """Lazy connector so the package can run locally without Neo4j installed."""

    def __init__(self, config: GraphConfig) -> None:
        self.config = config

    def create_driver(self):
        if not self.config.neo4j_uri or not self.config.neo4j_password:
            raise ConfigurationError(
                "Neo4j credentials are missing. Set neo4j_uri and neo4j_password."
            )
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise IntegrationUnavailableError("The neo4j package is not installed.") from exc
        return GraphDatabase.driver(
            self.config.neo4j_uri,
            auth=(self.config.neo4j_username, self.config.neo4j_password),
        )

    def reset_database(self, session: Any) -> None:
        """Clear data and drop user-created schema objects when reset is requested."""
        self._drop_constraints(session)
        self._drop_indexes(session)
        session.run("MATCH (n) DETACH DELETE n")

    @staticmethod
    def _drop_constraints(session: Any) -> None:
        result = session.run("SHOW CONSTRAINTS YIELD name RETURN name")
        for record in result:
            name = record["name"]
            session.run(f"DROP CONSTRAINT `{name}` IF EXISTS")

    @staticmethod
    def _drop_indexes(session: Any) -> None:
        result = session.run("SHOW INDEXES YIELD name, type, entityType RETURN name, type, entityType")
        for record in result:
            index_name = record["name"]
            index_type = str(record.get("type", "")).upper()
            if index_type == "LOOKUP":
                continue
            session.run(f"DROP INDEX `{index_name}` IF EXISTS")
