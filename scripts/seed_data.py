from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ingestion.service import IngestionService


RAW_ENTRIES = [
    "TypeError: undefined is not a function\nOccurred when clicking submit button in checkout.\nCause: forgot to bind this in a React class component.\nFix: switched handler to an arrow function.\nTech: React JavaScript",
    "NullPointerException in UserService.getUser\nCaused by: missing null check after repository lookup.\nFix: guard with Optional and return 404.\nStack: Java Spring PostgreSQL",
    "CORS error blocked by Access-Control-Allow-Origin\nFrontend cannot reach FastAPI backend from localhost:3000.\nFix: added CORSMiddleware with explicit origins.\nTech: React FastAPI Python",
    "TimeoutError while publishing job to queue\nCause: Redis host pointed to a stale container name.\nFix: updated docker-compose service alias and retried.\nStack: Python Redis Docker",
    "GraphQL resolver returned undefined for non-nullable field\nCause: resolver skipped authorization branch and returned None.\nFix: return fallback DTO and add auth guard.\nTech: Node GraphQL TypeScript",
    "Kubernetes CrashLoopBackOff on worker deployment\nCause: invalid environment variable name in secret mapping.\nFix: corrected manifest key and rolled restart.\nTech: Kubernetes Docker",
    "TypeError cannot read properties of undefined reading map\nCause: API response shape changed after backend pagination update.\nFix: defaulted list to empty array and updated serializer.\nTech: React TypeScript",
    "503 Service Unavailable from nginx upstream\nCause: backend container passed health check too early.\nFix: added startup probe and increased readiness delay.\nTech: nginx Docker FastAPI",
    "Memory leak during websocket stream handling\nCause: stale listeners were never removed after disconnect.\nFix: unsubscribe listeners in finally block.\nTech: Node WebSocket JavaScript",
    "SQLAlchemy DetachedInstanceError during background task\nCause: ORM object used outside session lifecycle.\nFix: materialized primitive fields before scheduling task.\nTech: Python FastAPI PostgreSQL",
]


async def main() -> None:
    service = IngestionService()
    print(f"Seeding {len(RAW_ENTRIES)} debugging entries...")
    for raw_input in RAW_ENTRIES:
        result = await service.ingest(raw_input)
        print(f"- {result.entry.id}: {result.entry.title}")
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
