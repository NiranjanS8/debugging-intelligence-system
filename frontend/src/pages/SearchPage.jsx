import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, SlidersHorizontal, Bug } from 'lucide-react';
import SearchBar from '../components/SearchBar';
import PillTab from '../components/PillTab';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';
import { queryDebug } from '../lib/api';

const techFilters = ['All', 'react', 'python', 'node', 'docker', 'postgresql', 'fastapi'];

export default function SearchPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTech, setActiveTech] = useState('All');
  const [showFilters, setShowFilters] = useState(false);
  const [topK, setTopK] = useState(10);
  const [minConfidence, setMinConfidence] = useState(0);

  const performSearch = async (q) => {
    if (!q || q.trim().length < 3) return;
    setLoading(true);
    try {
      const techStack = activeTech !== 'All' ? [activeTech] : null;
      const conf = minConfidence > 0 ? minConfidence : null;
      const data = await queryDebug(q, topK, null, techStack, conf);
      setResults(data);
      setSearchParams({ q });
    } catch (err) {
      console.error('Search failed:', err);
      setResults({ results: [], total_results: 0, query: q, message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q);
    }
  }, []);

  return (
    <div className="page-enter max-w-[1240px] mx-auto px-6 md:px-12 py-12 md:py-16">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-display-lg mb-3">Search</h1>
        <p className="text-body-lg text-mute">
          Hybrid semantic + lexical search across your debugging knowledge base.
        </p>
      </div>

      {/* Search bar */}
      <div className="flex gap-3 mb-6">
        <SearchBar
          value={query}
          onChange={setQuery}
          onSubmit={performSearch}
          placeholder="Describe the bug, error, or symptom..."
          className="flex-1"
        />
        <Button
          variant="tertiary"
          onClick={() => setShowFilters(!showFilters)}
          className="shrink-0"
        >
          <SlidersHorizontal size={16} />
          <span className="hidden sm:inline">Filters</span>
        </Button>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card variant="elevated" hover={false} className="mb-6">
          <div className="flex flex-col sm:flex-row gap-6">
            <div className="flex-1">
              <label className="text-body-sm-strong text-on-dark block mb-2">Results</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={1}
                  max={50}
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="flex-1 accent-primary"
                />
                <span className="text-body-sm text-mute w-8 text-right">{topK}</span>
              </div>
            </div>
            <div className="flex-1">
              <label className="text-body-sm-strong text-on-dark block mb-2">Min Confidence</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={minConfidence * 100}
                  onChange={(e) => setMinConfidence(Number(e.target.value) / 100)}
                  className="flex-1 accent-primary"
                />
                <span className="text-body-sm text-mute w-10 text-right">
                  {(minConfidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Tech filter pills */}
      <PillTab
        tabs={techFilters}
        activeTab={activeTech}
        onTabChange={setActiveTech}
        className="mb-8"
      />

      {/* Results */}
      {loading ? (
        <LoadingSpinner className="py-24" />
      ) : results === null ? (
        <EmptyState
          icon={Search}
          title="Start a search"
          description="Enter a query to find matching debug entries using hybrid semantic + lexical retrieval."
        />
      ) : results.results.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No results found"
          description={`No entries matched "${results.query}". Try different keywords or remove filters.`}
        />
      ) : (
        <div>
          <p className="text-body-sm text-mute mb-4">
            {results.total_results} result{results.total_results !== 1 ? 's' : ''} for "{results.query}"
          </p>
          <div className="flex flex-col gap-3">
            {results.results.map((r) => (
              <Card
                key={r.id}
                variant="store"
                onClick={() => navigate(`/knowledge/${r.id}`)}
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-md bg-surface-card border border-hairline flex items-center justify-center shrink-0">
                    <Bug size={20} className="text-accent-blue" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-body-strong text-on-dark">{r.title}</h3>
                      <span className="text-caption-sm text-mute shrink-0">
                        {(r.similarity_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <p className="text-body-sm text-mute mt-1 line-clamp-1">
                      {r.root_cause}
                    </p>
                    <div className="flex flex-wrap gap-1.5 mt-2.5">
                      {r.tech_stack?.slice(0, 3).map((tech) => (
                        <Badge key={tech} variant="info">{tech}</Badge>
                      ))}
                      {r.tags?.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="neutral">{tag}</Badge>
                      ))}
                      <Badge variant="success">
                        {(r.confidence * 100).toFixed(0)}% conf
                      </Badge>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
