"""Phase 1 verification script -- tests all foundation modules."""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def main():
    print("=" * 60)
    print("  DIS Phase 1 — Verification")
    print("=" * 60)
    errors = []

    # 1. Config
    print("\n[1/5] Testing config...")
    try:
        from app.config import get_settings, LLMProvider
        s = get_settings()
        assert s.app_name == "Debugging Intelligence System"
        assert s.llm_provider == LLMProvider.FALLBACK
        assert s.embedding_model == "all-MiniLM-L6-v2"
        print(f"  OK App: {s.app_name}")
        print(f"  OK Env: {s.app_env}")
        print(f"  OK LLM Provider: {s.llm_provider.value}")
        print(f"  OK ChromaDB path: {s.chroma_persist_path}")
        print(f"  OK KB path: {s.knowledge_base_path}")
    except Exception as e:
        errors.append(f"Config: {e}")
        print(f"  FAIL FAILED: {e}")

    # 2. Models
    print("\n[2/5] Testing models...")
    try:
        from app.models.debug_entry import (
            DebugAddRequest, StructuredDebugData, DebugEntry,
            DebugEntryResponse, SimilarEntry,
        )
        # Test DebugAddRequest validation
        req = DebugAddRequest(raw_input="TypeError: undefined is not a function in React component")
        assert len(req.raw_input) > 10
        print(f"  OK DebugAddRequest validated")

        # Test StructuredDebugData with tag normalization
        structured = StructuredDebugData(
            title="React Error",
            symptoms=["crash", "white screen"],
            root_cause="incorrect this binding",
            fix="use arrow function",
            tags="React, JavaScript",  # comma-separated string
            tech_stack=["React", "JavaScript"],
            confidence=0.85,
        )
        assert structured.tags == ["react", "javascript"]
        assert structured.tech_stack == ["react", "javascript"]
        print(f"  OK StructuredDebugData + tag normalization")

        # Test DebugEntry
        entry = DebugEntry(
            id="abc123def456",
            title="Test",
            root_cause="test cause",
            fix="test fix",
        )
        assert entry.category == "uncategorized"
        assert entry.update_count == 0
        print(f"  OK DebugEntry defaults")

        from app.models.query import DebugQueryRequest, DebugQueryResponse, QueryResult
        print(f"  OK Query models imported")

        from app.models.analytics import (
            ClusterInfo, ClusterResponse, AnalyticsSummary,
            FailurePatternResponse, PatternStat,
        )
        print(f"  OK Analytics models imported")

    except Exception as e:
        errors.append(f"Models: {e}")
        print(f"  FAIL FAILED: {e}")

    # 3. Logger
    print("\n[3/5] Testing logger...")
    try:
        from app.utils.logger import get_logger
        logger = get_logger("test.verify")
        logger.info("Phase 1 verification log entry", extra={"operation": "verify"})
        print(f"  OK Logger works (JSON format)")
    except Exception as e:
        errors.append(f"Logger: {e}")
        print(f"  FAIL FAILED: {e}")

    # 4. ID Generator
    print("\n[4/5] Testing ID generator...")
    try:
        from app.utils.id_generator import generate_entry_id, generate_content_hash

        id1 = generate_entry_id("React Undefined Error", "incorrect this binding")
        id2 = generate_entry_id("React Undefined Error", "incorrect this binding")
        id3 = generate_entry_id("Different Title", "different cause")
        assert id1 == id2, "Same input must produce same ID"
        assert id1 != id3, "Different input must produce different ID"
        assert len(id1) == 12
        print(f"  OK Deterministic ID: {id1}")
        print(f"  OK Different ID:     {id3}")

        h = generate_content_hash("test content")
        assert len(h) == 64
        print(f"  OK Content hash: {h[:24]}...")
    except Exception as e:
        errors.append(f"ID Generator: {e}")
        print(f"  FAIL FAILED: {e}")

    # 5. Text Processing
    print("\n[5/5] Testing text processing...")
    try:
        from app.utils.text_processing import (
            infer_category, normalize_text, build_embedding_document,
            generate_slug, extract_error_type,
        )

        assert infer_category(["react"], ["runtime"]) == "frontend"
        assert infer_category(["python", "fastapi"], []) == "backend"
        assert infer_category(["docker", "k8s"], []) == "infra"
        assert infer_category(["unknown"], []) == "uncategorized"
        print(f"  OK Category inference (frontend/backend/infra/uncategorized)")

        slug = generate_slug("React Undefined Function Error")
        assert slug == "react-undefined-function-error"
        print(f"  OK Slug: {slug}")

        err = extract_error_type("TypeError: undefined is not a function")
        assert err == "TypeError"
        print(f"  OK Error extraction: {err}")

        doc = build_embedding_document(
            "React Error", "wrong binding", "use arrow fn", ["crash"], ["react"]
        )
        assert "Title:" in doc and "Root Cause:" in doc
        print(f"  OK Embedding doc: {doc[:60]}...")

        normalized = normalize_text("  hello   world  \r\n  test  ")
        assert "   " not in normalized  # no triple spaces remain
        print(f"  OK Text normalization")

    except Exception as e:
        errors.append(f"Text Processing: {e}")
        print(f"  FAIL FAILED: {e}")

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"  FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"    FAIL {e}")
        sys.exit(1)
    else:
        print("  OK ALL PHASE 1 CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
