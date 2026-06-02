const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  const res = await fetch(url, config);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json();
}

// ── System ──
export const healthCheck = () => request('/health');

// ── Debug ──
export const addDebugEntry = (rawInput) =>
  request('/debug/add', {
    method: 'POST',
    body: JSON.stringify({ raw_input: rawInput }),
  });

export const queryDebug = (query, topK = 5, tags = null, techStack = null, minConfidence = null) =>
  request('/debug/query', {
    method: 'POST',
    body: JSON.stringify({
      query,
      top_k: topK,
      ...(tags && { tags }),
      ...(techStack && { tech_stack: techStack }),
      ...(minConfidence !== null && { min_confidence: minConfidence }),
    }),
  });

export const getSimilar = (entryId, topK = 5) =>
  request(`/debug/similar/${entryId}?top_k=${topK}`);

export const explainDebug = (rawInput, topK = 3, includeGraphContext = true) =>
  request('/debug/explain', {
    method: 'POST',
    body: JSON.stringify({
      raw_input: rawInput,
      top_k: topK,
      include_graph_context: includeGraphContext,
    }),
  });

// ── Analytics ──
export const getAnalyticsSummary = () => request('/analytics/summary');

export const getFailurePatterns = (limit = 5) =>
  request(`/analytics/patterns?limit=${limit}`);

export const clusterEntries = (category = null) =>
  request('/analytics/cluster', {
    method: 'POST',
    ...(category && { body: JSON.stringify({}), }),
  });

// ── Knowledge ──
export const listKnowledge = (category = null) =>
  request(`/knowledge/list${category ? `?category=${category}` : ''}`);

export const getKnowledgeEntry = (id) => request(`/knowledge/${id}`);

// ── Graph ──
export const getGraphSummary = () => request('/graph/summary');

export const getGraphEntry = (id) => request(`/graph/entry/${id}`);
