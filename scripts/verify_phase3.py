"""Phase 3 verification: add entries, semantic search, similarity lookup."""
import sys, os, json, httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE = "http://localhost:8000"

ENTRIES = [
    "TypeError: undefined is not a function\nOccurred when clicking submit button.\nThe onClick handler referenced this.handleSubmit but was undefined.\nFix: forgot to bind this in React component. Used arrow function.",

    "NullPointerException in UserService.getUser()\nCaused by: missing null check on database query result.\nFix: Added Optional wrapper and null check. Added 404 response in controller.\nStack: Java, Spring Boot, PostgreSQL",

    "CORS error: blocked by Access-Control-Allow-Origin\nFrontend React app cannot reach the FastAPI backend on a different port.\nFix: added CORSMiddleware to FastAPI with allow_origins=['*'].\nTech: React, FastAPI, Python",
]


def add_entries():
    print("=== Adding 3 debug entries ===")
    ids = []
    for i, raw in enumerate(ENTRIES, 1):
        resp = httpx.post(f"{BASE}/debug/add", json={"raw_input": raw}, timeout=120)
        data = resp.json()
        entry = data["entry"]
        similar_count = len(data.get("similar_entries", []))
        print(f"  [{i}] {entry['title']}")
        print(f"      id={entry['id']}  category={entry['category']}  tech={entry['tech_stack']}  similar={similar_count}")
        ids.append(entry["id"])
    return ids


def test_semantic_search():
    print("\n=== Semantic Search ===")

    queries = [
        "null reference errors in Java",
        "this binding issues in React",
        "CORS configuration problems",
    ]
    for q in queries:
        resp = httpx.post(f"{BASE}/debug/query", json={"query": q, "top_k": 3}, timeout=30)
        data = resp.json()
        print(f"\n  Query: '{q}'")
        for r in data["results"]:
            print(f"    -> {r['title']} (score={r['similarity_score']})")


def test_similarity(ids):
    print("\n=== Similar Entries ===")
    for eid in ids:
        resp = httpx.get(f"{BASE}/debug/similar/{eid}?top_k=3", timeout=30)
        if resp.status_code == 200:
            results = resp.json()
            print(f"\n  Similar to {eid}:")
            for r in results:
                print(f"    -> {r['title']} (score={r['similarity_score']})")
        elif resp.status_code == 404:
            print(f"\n  {eid}: no similar entries (expected for small KB)")


if __name__ == "__main__":
    ids = add_entries()
    test_semantic_search()
    test_similarity(ids)
    print("\n=== Phase 3 verification complete ===")
