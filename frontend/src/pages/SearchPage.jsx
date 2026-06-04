import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search,
  SlidersHorizontal,
  Bug,
  RotateCcw,
  ChevronDown,
  ArrowUpDown,
  Check,
  Filter,
  X,
} from 'lucide-react';
import SearchBar from '../components/SearchBar';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';
import { queryDebug } from '../lib/api';

/* ── Static data ── */
const TECHNOLOGIES = [
  'react', 'python', 'node', 'docker', 'postgresql',
  'fastapi', 'typescript', 'go', 'java', 'rust',
];

const TAGS = [
  'null-error', 'undefined-error', 'timeout', 'async-issue',
  'crash', 'memory-issue', 'permissions', 'auth-error',
  'type-error', 'import-error',
];

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance (Match %)' },
  { value: 'confidence', label: 'LLM Confidence' },
];

/* ── Reusable checkbox component ── */
function CheckboxItem({ label, checked, onChange }) {
  return (
    <label
      className="flex items-center gap-2 cursor-pointer group select-none"
      style={{ padding: '3px 0' }}
    >
      <span
        className={`
          w-4 h-4 rounded-xs border flex items-center justify-center shrink-0 transition-all duration-150
          ${checked
            ? 'bg-accent-blue border-accent-blue'
            : 'bg-transparent border-hairline-strong group-hover:border-mute'
          }
        `.trim()}
      >
        {checked && <Check size={11} strokeWidth={3} className="text-canvas" />}
      </span>
      <span className={`text-body-sm transition-colors duration-150 ${checked ? 'text-on-dark' : 'text-mute group-hover:text-body'}`}>
        {label}
      </span>
    </label>
  );
}

/* ── Sort dropdown ── */
function SortDropdown({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const current = SORT_OPTIONS.find((o) => o.value === value);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-md border border-hairline bg-surface-elevated text-body-sm text-on-dark hover:border-hairline-strong transition-colors duration-150 cursor-pointer w-full"
      >
        <ArrowUpDown size={14} className="text-mute shrink-0" />
        <span className="flex-1 text-left truncate">{current?.label}</span>
        <ChevronDown size={14} className={`text-mute transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-full bg-surface-elevated border border-hairline rounded-md shadow-lg z-30 overflow-hidden">
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => { onChange(opt.value); setOpen(false); }}
              className={`
                w-full text-left px-3 py-2 text-body-sm cursor-pointer transition-colors duration-100
                ${opt.value === value
                  ? 'bg-accent-blue-soft text-accent-blue'
                  : 'text-mute hover:text-on-dark hover:bg-surface-card'
                }
              `.trim()}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Slider component ── */
function FilterSlider({ label, value, min, max, step = 1, suffix = '', onChange, displayValue }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="text-body-sm-strong text-on-dark">{label}</label>
        <span className="text-caption-sm text-accent-blue font-medium tabular-nums">
          {displayValue ?? value}{suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-accent-blue"
        style={{ height: '4px' }}
      />
    </div>
  );
}

/* ═══════════════ Main Page ═══════════════ */
export default function SearchPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  /* ── Core state ── */
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [rawResults, setRawResults] = useState(null);
  const [loading, setLoading] = useState(false);

  /* ── Filter state ── */
  const [showFilters, setShowFilters] = useState(false);
  const [topK, setTopK] = useState(10);
  const [minConfidence, setMinConfidence] = useState(0);
  const [minSimilarity, setMinSimilarity] = useState(0);
  const [selectedTechs, setSelectedTechs] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [sortBy, setSortBy] = useState('relevance');

  const hasActiveFilters = selectedTechs.length > 0 || selectedTags.length > 0 || minSimilarity > 0 || sortBy !== 'relevance' || minConfidence > 0;

  /* ── Toggle helpers ── */
  const toggleTech = useCallback((tech) => {
    setSelectedTechs((prev) =>
      prev.includes(tech) ? prev.filter((t) => t !== tech) : [...prev, tech]
    );
  }, []);

  const toggleTag = useCallback((tag) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }, []);

  const resetFilters = useCallback(() => {
    setSelectedTechs([]);
    setSelectedTags([]);
    setMinSimilarity(0);
    setMinConfidence(0);
    setSortBy('relevance');
    setTopK(10);
  }, []);

  /* ── Search ── */
  const performSearch = useCallback(async (q) => {
    if (!q || q.trim().length < 3) return;
    setLoading(true);
    try {
      const techStack = selectedTechs.length > 0 ? selectedTechs : null;
      const tags = selectedTags.length > 0 ? selectedTags : null;
      const conf = minConfidence > 0 ? minConfidence : null;
      const data = await queryDebug(q, topK, tags, techStack, conf);
      setRawResults(data);
      setSearchParams({ q });
    } catch (err) {
      console.error('Search failed:', err);
      setRawResults({ results: [], total_results: 0, query: q, message: err.message });
    } finally {
      setLoading(false);
    }
  }, [topK, selectedTechs, selectedTags, minConfidence, setSearchParams]);

  /* ── Initial load ── */
  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q);
    }
  }, []);

  /* ── Re-search on filter change (only if we already have a query) ── */
  useEffect(() => {
    if (query && query.trim().length >= 3 && rawResults !== null) {
      performSearch(query);
    }
  }, [topK, selectedTechs, selectedTags, minConfidence]);

  /* ── Client-side filter & sort ── */
  const filteredResults = useMemo(() => {
    if (!rawResults?.results) return null;

    let items = [...rawResults.results];

    // Client-side similarity threshold
    if (minSimilarity > 0) {
      items = items.filter((r) => (r.similarity_score ?? 0) >= minSimilarity / 100);
    }

    // Sort
    if (sortBy === 'confidence') {
      items.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
    } else {
      items.sort((a, b) => (b.similarity_score ?? 0) - (a.similarity_score ?? 0));
    }

    return items;
  }, [rawResults, minSimilarity, sortBy]);

  const activeFilterCount = selectedTechs.length + selectedTags.length + (minSimilarity > 0 ? 1 : 0) + (minConfidence > 0 ? 1 : 0) + (sortBy !== 'relevance' ? 1 : 0);

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
          className={`shrink-0 ${showFilters ? '!border-accent-blue !text-accent-blue' : ''}`}
        >
          <Filter size={16} />
          <span className="hidden sm:inline">Filters</span>
          {activeFilterCount > 0 && (
            <span className="ml-1 w-5 h-5 rounded-full bg-accent-blue text-canvas text-caption-sm flex items-center justify-center font-medium">
              {activeFilterCount}
            </span>
          )}
        </Button>
      </div>

      {/* ═══ Advanced Filters Panel ═══ */}
      {showFilters && (
        <div
          className="mb-8 rounded-lg border border-hairline bg-surface-elevated overflow-hidden"
          style={{ animation: 'fadeInUp 0.2s ease-out' }}
        >
          {/* Panel header */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-hairline">
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={15} className="text-accent-blue" />
              <span className="text-body-sm-strong text-on-dark">Advanced Filters</span>
              {hasActiveFilters && (
                <Badge variant="info">{activeFilterCount} active</Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              {hasActiveFilters && (
                <button
                  onClick={resetFilters}
                  className="flex items-center gap-1 text-caption-sm text-mute hover:text-accent-red transition-colors cursor-pointer"
                >
                  <RotateCcw size={12} />
                  Reset
                </button>
              )}
              <button
                onClick={() => setShowFilters(false)}
                className="text-mute hover:text-on-dark transition-colors cursor-pointer p-1"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Filter columns */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-0 divide-y sm:divide-y-0 sm:divide-x divide-hairline">

            {/* Column 1: Sliders */}
            <div className="p-5 flex flex-col gap-5">
              <h4 className="text-caption-sm text-mute uppercase tracking-wider">Sliders & Metrics</h4>
              <FilterSlider
                label="Max Results"
                value={topK}
                min={1}
                max={50}
                onChange={setTopK}
                suffix=""
                displayValue={topK}
              />
              <FilterSlider
                label="Min Confidence"
                value={Math.round(minConfidence * 100)}
                min={0}
                max={100}
                onChange={(v) => setMinConfidence(v / 100)}
                suffix="%"
              />
              <FilterSlider
                label="Min Similarity"
                value={minSimilarity}
                min={0}
                max={100}
                onChange={setMinSimilarity}
                suffix="%"
              />
            </div>

            {/* Column 2: Technologies */}
            <div className="p-5 flex flex-col gap-2">
              <h4 className="text-caption-sm text-mute uppercase tracking-wider mb-1">Technology Stack</h4>
              <div className="flex flex-col gap-0.5 max-h-[200px] overflow-y-auto pr-1">
                {TECHNOLOGIES.map((tech) => (
                  <CheckboxItem
                    key={tech}
                    label={tech}
                    checked={selectedTechs.includes(tech)}
                    onChange={() => toggleTech(tech)}
                  />
                ))}
              </div>
              {selectedTechs.length > 0 && (
                <button
                  onClick={() => setSelectedTechs([])}
                  className="text-caption-sm text-mute hover:text-accent-blue transition-colors mt-1 cursor-pointer text-left"
                >
                  Clear ({selectedTechs.length})
                </button>
              )}
            </div>

            {/* Column 3: Tags */}
            <div className="p-5 flex flex-col gap-2">
              <h4 className="text-caption-sm text-mute uppercase tracking-wider mb-1">Diagnostic Tags</h4>
              <div className="flex flex-col gap-0.5 max-h-[200px] overflow-y-auto pr-1">
                {TAGS.map((tag) => (
                  <CheckboxItem
                    key={tag}
                    label={tag}
                    checked={selectedTags.includes(tag)}
                    onChange={() => toggleTag(tag)}
                  />
                ))}
              </div>
              {selectedTags.length > 0 && (
                <button
                  onClick={() => setSelectedTags([])}
                  className="text-caption-sm text-mute hover:text-accent-blue transition-colors mt-1 cursor-pointer text-left"
                >
                  Clear ({selectedTags.length})
                </button>
              )}
            </div>

            {/* Column 4: Sort */}
            <div className="p-5 flex flex-col gap-4">
              <h4 className="text-caption-sm text-mute uppercase tracking-wider">Sort Results</h4>
              <SortDropdown value={sortBy} onChange={setSortBy} />
              <p className="text-caption-sm text-mute leading-relaxed">
                {sortBy === 'relevance'
                  ? 'Results are ordered by semantic similarity match score.'
                  : 'Results are ordered by LLM-assigned confidence rating.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Active filter chips strip */}
      {(selectedTechs.length > 0 || selectedTags.length > 0) && !showFilters && (
        <div className="flex flex-wrap items-center gap-2 mb-6">
          <span className="text-caption-sm text-mute">Active:</span>
          {selectedTechs.map((tech) => (
            <button
              key={tech}
              onClick={() => toggleTech(tech)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-accent-blue-soft text-accent-blue text-caption-sm cursor-pointer hover:bg-accent-blue hover:text-canvas transition-colors"
            >
              {tech}
              <X size={10} />
            </button>
          ))}
          {selectedTags.map((tag) => (
            <button
              key={tag}
              onClick={() => toggleTag(tag)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-elevated text-mute text-caption-sm cursor-pointer hover:bg-hairline-strong hover:text-on-dark transition-colors"
            >
              {tag}
              <X size={10} />
            </button>
          ))}
          <button
            onClick={resetFilters}
            className="text-caption-sm text-mute hover:text-accent-red transition-colors cursor-pointer ml-1"
          >
            Clear all
          </button>
        </div>
      )}

      {/* ═══ Results ═══ */}
      {loading ? (
        <LoadingSpinner className="py-24" />
      ) : rawResults === null ? (
        <EmptyState
          icon={Search}
          title="Start a search"
          description="Enter a query to find matching debug entries using hybrid semantic + lexical retrieval."
        />
      ) : filteredResults && filteredResults.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No results found"
          description={
            minSimilarity > 0 || hasActiveFilters
              ? 'No entries matched your current filters. Try lowering the similarity threshold or removing filters.'
              : `No entries matched "${rawResults.query}". Try different keywords.`
          }
        />
      ) : filteredResults ? (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-body-sm text-mute">
              {filteredResults.length} result{filteredResults.length !== 1 ? 's' : ''}
              {filteredResults.length !== rawResults.total_results && (
                <span className="text-ash"> of {rawResults.total_results}</span>
              )}
              {' '}for "{rawResults.query}"
            </p>
            {!showFilters && (
              <span className="text-caption-sm text-ash">
                Sorted by {sortBy === 'relevance' ? 'relevance' : 'confidence'}
              </span>
            )}
          </div>
          <div className="flex flex-col gap-3">
            {filteredResults.map((r) => (
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
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-caption-sm text-accent-blue font-medium tabular-nums">
                          {(r.similarity_score * 100).toFixed(0)}%
                        </span>
                        <span className="text-caption-sm text-mute">match</span>
                      </div>
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
      ) : null}
    </div>
  );
}
