import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, AlertTriangle, CheckCircle2, Bug, Loader2, Plus } from 'lucide-react';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';
import { addDebugEntry } from '../lib/api';

export default function AddEntryPage() {
  const navigate = useNavigate();
  const [rawInput, setRawInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (rawInput.trim().length < 10) {
      setError('Input must be at least 10 characters.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await addDebugEntry(rawInput);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const hasStarted = loading || result;

  return (
    <div className="page-enter max-w-[1240px] mx-auto px-6 md:px-12 py-12 md:py-16">
      {/* State A: Initial State - Centered focused layout */}
      {!hasStarted ? (
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-display-lg mb-3">Add Incident</h1>
            <p className="text-body-lg text-mute">
              Paste raw debugging input: stack traces, error logs, notes, and fixes. The system will structure, index, and deduplicate it.
            </p>
          </div>

          <Card variant="surface" hover={false}>
            <label className="text-body-sm-strong text-on-dark block mb-3">
              Raw Debug Input
            </label>
            <textarea
              value={rawInput}
              onChange={(e) => setRawInput(e.target.value)}
              placeholder={`TypeError: undefined is not a function\n  at UserComponent.render (UserComponent.js:42)\n  at processChild (react-dom.js:1234)\n\nFix: forgot to bind 'this' in React component constructor\nTags: react, javascript, binding`}
              rows={16}
              className="
                w-full p-4
                bg-surface-elevated text-on-dark
                border border-hairline rounded-md
                text-body-md font-mono
                placeholder:text-stone
                outline-none resize-y
                focus:border-hairline-strong
                transition-colors duration-150
              "
            />

            <div className="flex items-center justify-between mt-4 pt-4 border-t border-hairline-soft">
              <span className="text-caption-sm text-stone">
                {rawInput.length} characters · min 10
              </span>
              <Button
                onClick={handleSubmit}
                disabled={loading || rawInput.trim().length < 10}
                variant={loading || rawInput.trim().length < 10 ? 'disabled' : 'primary'}
              >
                <Send size={14} />
                Analyze & Add
              </Button>
            </div>

            {error && (
              <div className="flex items-start gap-2 mt-4 p-3 bg-accent-red-soft rounded-md">
                <AlertTriangle size={16} className="text-accent-red mt-0.5 shrink-0" />
                <p className="text-body-sm text-accent-red">{error}</p>
              </div>
            )}
          </Card>
        </div>
      ) : (
        /* State B: Active State - Workspace Layout */
        <div>
          {/* Workspace Header */}
          <div className="flex items-center justify-between mb-8 pb-4 border-b border-hairline-soft">
            <div>
              <h1 className="text-display-lg mb-1">Add Incident</h1>
              <p className="text-body-md text-mute">
                Structuring, indexing, and deduplicating your raw incident logs.
              </p>
            </div>
            {result && (
              <Button
                variant="tertiary"
                onClick={() => {
                  setResult(null);
                  setError(null);
                }}
              >
                <Plus size={14} />
                New Incident
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input (Left) */}
            <div>
              <Card variant="surface" hover={false}>
                <label className="text-body-sm-strong text-on-dark block mb-3">
                  Raw Debug Input
                </label>
                <textarea
                  value={rawInput}
                  onChange={(e) => setRawInput(e.target.value)}
                  placeholder={`TypeError: undefined is not a function\n  at UserComponent.render (UserComponent.js:42)\n  at processChild (react-dom.js:1234)\n\nFix: forgot to bind 'this' in React component constructor\nTags: react, javascript, binding`}
                  rows={14}
                  className="
                    w-full p-4
                    bg-surface-elevated text-on-dark
                    border border-hairline rounded-md
                    text-body-md font-mono
                    placeholder:text-stone
                    outline-none resize-y
                    focus:border-hairline-strong
                    transition-colors duration-150
                  "
                />

                <div className="flex items-center justify-between mt-4 pt-4 border-t border-hairline-soft">
                  <span className="text-caption-sm text-stone">
                    {rawInput.length} characters · min 10
                  </span>
                  <Button
                    onClick={handleSubmit}
                    disabled={loading || rawInput.trim().length < 10}
                    variant={loading || rawInput.trim().length < 10 ? 'disabled' : 'primary'}
                  >
                    {loading ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Send size={14} />
                        Analyze & Add
                      </>
                    )}
                  </Button>
                </div>

                {error && (
                  <div className="flex items-start gap-2 mt-4 p-3 bg-accent-red-soft rounded-md">
                    <AlertTriangle size={16} className="text-accent-red mt-0.5 shrink-0" />
                    <p className="text-body-sm text-accent-red">{error}</p>
                  </div>
                )}
              </Card>
            </div>

            {/* Result (Right) */}
            <div>
              {loading ? (
                <Card variant="elevated" hover={false} className="flex flex-col items-center justify-center min-h-[400px]">
                  <Loader2 size={36} className="text-accent-blue animate-spin mb-4" />
                  <h3 className="text-heading-sm text-ink mb-2">Analyzing Incident</h3>
                  <p className="text-body-sm text-mute max-w-xs text-center">
                    Using LLM agents to extract title, symptoms, root cause, fix, and tags from your raw debugging data...
                  </p>
                </Card>
              ) : result ? (
                <div className="space-y-4">
                  {/* Success header */}
                  <Card variant="elevated" hover={false}>
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-md bg-accent-green-soft flex items-center justify-center shrink-0">
                        <CheckCircle2 size={20} className="text-accent-green" />
                      </div>
                      <div>
                        <h3 className="text-body-strong text-on-dark">{result.message}</h3>
                        <p className="text-caption-sm text-mute mt-1">
                          Projection: {result.projection_status}
                        </p>
                      </div>
                    </div>
                  </Card>

                  {/* Duplicate warning */}
                  {result.is_duplicate && (
                    <Card variant="surface" hover={false} className="border-accent-yellow/30">
                      <div className="flex items-start gap-3">
                        <AlertTriangle size={18} className="text-accent-yellow mt-0.5 shrink-0" />
                        <div>
                          <h4 className="text-body-sm-strong text-accent-yellow">Possible Duplicate</h4>
                          <p className="text-body-sm text-mute mt-1">
                            This entry may be a duplicate of <strong className="text-on-dark">{result.duplicate_of}</strong>
                          </p>
                          {result.duplicate_entry && (
                            <button
                              onClick={() => navigate(`/knowledge/${result.duplicate_entry.id}`)}
                              className="text-body-sm text-accent-blue hover:underline mt-1 cursor-pointer"
                            >
                              View original →
                            </button>
                          )}
                        </div>
                      </div>
                    </Card>
                  )}

                  {/* Structured entry */}
                  <Card variant="surface" hover={false}>
                    <h3 className="text-heading-sm mb-4">{result.entry.title}</h3>

                    <div className="flex flex-wrap gap-1.5 mb-4">
                      <Badge variant="pro">{result.entry.category}</Badge>
                      <Badge variant="success">
                        {((result.entry.confidence || 0) * 100).toFixed(0)}% confidence
                      </Badge>
                      {result.entry.tech_stack?.map((t) => (
                        <Badge key={t} variant="info">{t}</Badge>
                      ))}
                      {result.entry.tags?.map((t) => (
                        <Badge key={t} variant="neutral">{t}</Badge>
                      ))}
                    </div>

                    <div className="space-y-3 border-t border-hairline-soft pt-4">
                      {result.entry.symptoms?.length > 0 && (
                        <div>
                          <span className="text-caption-sm text-mute uppercase tracking-wider">Symptoms</span>
                          <ul className="list-disc list-inside text-body-sm text-body mt-1 space-y-0.5">
                            {result.entry.symptoms.map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div>
                        <span className="text-caption-sm text-mute uppercase tracking-wider">Root Cause</span>
                        <p className="text-body-sm text-body mt-1">{result.entry.root_cause}</p>
                      </div>
                      <div>
                        <span className="text-caption-sm text-mute uppercase tracking-wider">Fix</span>
                        <p className="text-body-sm text-body mt-1">{result.entry.fix}</p>
                      </div>
                    </div>

                    <Button
                      variant="secondary"
                      size="sm"
                      className="mt-6"
                      onClick={() => navigate(`/knowledge/${result.entry.id}`)}
                    >
                      View Full Entry →
                    </Button>
                  </Card>

                  {/* Similar entries */}
                  {result.similar_entries?.length > 0 && (
                    <Card variant="elevated" hover={false}>
                      <h4 className="text-body-sm-strong text-on-dark mb-3">
                        Similar Entries Found
                      </h4>
                      <div className="space-y-2">
                        {result.similar_entries.map((s) => (
                          <button
                            key={s.id}
                            onClick={() => navigate(`/knowledge/${s.id}`)}
                            className="w-full text-left flex items-start gap-3 p-2.5 rounded-sm hover:bg-surface-card transition-colors duration-100 cursor-pointer"
                          >
                            <div className="w-8 h-8 rounded-md bg-surface-card border border-hairline flex items-center justify-center shrink-0">
                              <Bug size={14} className="text-accent-blue" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <span className="text-body-sm text-on-dark block truncate">{s.title}</span>
                              <span className="text-caption-sm text-mute">
                                {(s.similarity_score * 100).toFixed(0)}% similar
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </Card>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
