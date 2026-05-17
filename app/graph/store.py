from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GraphStore:
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.neo4j_enabled
        self._driver = None
        if self.enabled:
            self._connect()

    def _connect(self) -> None:
        try:
            from neo4j import GraphDatabase  # type: ignore
        except ImportError:
            logger.warning(
                "Neo4j support requested but dependency is not installed",
                extra={"operation": "graph_connect"},
            )
            self.enabled = False
            return

        self._driver = GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_user, self.settings.neo4j_password),
        )
        logger.info(
            "Neo4j driver initialized",
            extra={"operation": "graph_connect", "uri": self.settings.neo4j_uri},
        )

    def ensure_schema(self) -> None:
        if not self.enabled or self._driver is None:
            return

        statements = [
            "CREATE CONSTRAINT bug_id_unique IF NOT EXISTS FOR (b:Bug) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT root_cause_name_unique IF NOT EXISTS FOR (r:RootCause) REQUIRE r.name IS UNIQUE",
            "CREATE CONSTRAINT tech_name_unique IF NOT EXISTS FOR (t:Tech) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT symptom_name_unique IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
        ]
        for statement in statements:
            self.run(statement)

    def run(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not self.enabled or self._driver is None:
            return []

        with self._driver.session(database=self.settings.neo4j_database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
