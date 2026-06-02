import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Lightbulb, Send, Loader2, CheckCircle2, AlertTriangle,
  ArrowRight, Bug, GitFork, Plus,
} from 'lucide-react';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';
import { explainDebug } from '../lib/api';

export default function ExplainPage() {
  const navigate = useNavigate();
  const [rawInput, setRawInput] = useState('');
  const [topK, setTopK] = useState(3);
  const [includeGraph, setIncludeGraph] = useState(true);
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
      const data = await explainDebug(rawInput, topK, includeGraph);
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
      {/* State A: Initial state - focused, centered input (chat style) */}
      {!hasStarted ? (
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-display-lg mb-3">AI-Powered Explanation</h1>
            <p className="text-body-lg text-mute">
              Describe your issue or paste an error log. The system will retrieve relevant historical incidents and generate a grounded explanation.
            </p>
          </div>

          <Card variant="surface" hover={false}>
            <label className="text-body-sm-strong text-on-dark block mb-3">
              Describe the Issue
            </label>
            <textarea
              value={rawInput}
              onChange={(e) => setRawInput(e.target.value)}
              placeholder="Paste the error, stack trace, or describe the symptom..."
              rows={12}
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

            {/* Options Row */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-6 pt-4 border-t border-hairline-soft">
              <div className="flex flex-wrap gap-6">
                <div className="flex items-center gap-2">
                  <label className="text-body-sm text-body">Evidence count</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min={1}
                      max={10}
                      value={topK}
                      onChange={(e) => setTopK(Number(e.target.value))}
                      className="w-24 accent-primary"
                    />
                    <span className="text-body-sm text-mute w-5 text-right">{topK}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3">
                  <label className="text-body-sm text-body">Include graph context</label>
                  <button
                    onClick={() => setIncludeGraph(!includeGraph)}
                    className={`
                      w-10 h-5 rounded-full transition-colors duration-200 cursor-pointer
                      ${includeGraph ? 'bg-primary' : 'bg-surface-card border border-hairline'}
                    `}
                  >
                    <div
                      className={`
                        w-4 h-4 rounded-full transition-transform duration-200
                        ${includeGraph ? 'translate-x-5 bg-on-primary' : 'translate-x-0.5 bg-mute'}
                      `}
                    />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-4">
                <span className="text-caption-sm text-stone">
                  {rawInput.length} chars
                </span>
                <Button
                  onClick={handleSubmit}
                  disabled={loading || rawInput.trim().length < 10}
                  variant={loading || rawInput.trim().length < 10 ? 'disabled' : 'primary'}
                >
                  <Lightbulb size={14} />
                  Explain
                </Button>
              </div>
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
        /* State B: Active state - split-screen workspace */
        <div>
          {/* Header */}
          <div className="flex items-center justify-between mb-8 pb-4 border-b border-hairline-soft">
            <div>
              <h1 className="text-display-lg mb-1">AI-Powered Explanation</h1>
              <p className="text-body-md text-mute">
                Analyzing the issue with grounding evidence from your knowledge base.
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
                New Explanation
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Input panel (Left) */}
            <div className="lg:col-span-2">
              <Card variant="surface" hover={false}>
                <label className="text-body-sm-strong text-on-dark block mb-3">
                  Describe the Issue
                </label>
                <textarea
                  value={rawInput}
                  onChange={(e) => setRawInput(e.target.value)}
                  placeholder="Paste the error, stack trace, or describe the symptom..."
                  rows={10}
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

                {/* Options */}
                <div className="flex flex-col gap-4 mt-4">
                  <div className="flex items-center justify-between">
                    <label className="text-body-sm text-body">Evidence count</label>
                    <div className="flex items-center gap-2">
                      <input
                        type="range"
                        min={1}
                        max={10}
                        value={topK}
                        onChange={(e) => setTopK(Number(e.target.value))}
                        className="w-24 accent-primary"
                      />
                      <span className="text-body-sm text-mute w-5 text-right">{topK}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <label className="text-body-sm text-body">Include graph context</label>
                    <button
                      onClick={() => setIncludeGraph(!includeGraph)}
                      className={`
                        w-10 h-5 rounded-full transition-colors duration-200 cursor-pointer
                        ${includeGraph ? 'bg-primary' : 'bg-surface-card border border-hairline'}
                      `}
                    >
                      <div
                        className={`
                          w-4 h-4 rounded-full transition-transform duration-200
                          ${includeGraph ? 'translate-x-5 bg-on-primary' : 'translate-x-0.5 bg-mute'}
                        `}
                      />
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-5 pt-4 border-t border-hairline-soft">
                  <span className="text-caption-sm text-stone">
                    {rawInput.length} chars
                  </span>
                  <Button
                    onClick={handleSubmit}
                    disabled={loading || rawInput.trim().length < 10}
                    variant={loading || rawInput.trim().length < 10 ? 'disabled' : 'primary'}
                  >
                    {loading ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Lightbulb size={14} />
                        Explain
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

            {/* Result panel (Right) */}
            <div className="lg:col-span-3">
              {loading ? (
                <Card variant="elevated" hover={false} className="flex flex-col items-center justify-center min-h-[500px]">
                  <Loader2 size={36} className="text-accent-blue animate-spin mb-4" />
                  <h3 className="text-heading-sm text-ink mb-2">Generating Explanation</h3>
                  <p className="text-body-sm text-mute max-w-xs text-center">
                    Searching your knowledge base for historical evidence and building a grounded analysis...
                  </p>
                </Card>
              ) : result ? (
                <div className="space-y-4">
                  {/* Summary */}
                  <Card variant="elevated" hover={false}>
                    <div className="flex items-start gap-3 mb-4">
                      <div className="w-10 h-10 rounded-md bg-accent-blue-soft flex items-center justify-center shrink-0">
                        <Lightbulb size={20} className="text-accent-blue" />
                      </div>
                      <div>
                        <h3 className="text-heading-sm">Explanation</h3>
                        <Badge variant="success" className="mt-1">
                          {((result.confidence || 0) * 100).toFixed(0)}% confidence
                        </Badge>
                      </div>
                    </div>
                    <p className="text-body-md text-body leading-relaxed">{result.summary}</p>
                  </Card>

                  {/* Root cause & Fix */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card variant="surface" hover={false}>
                      <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle size={14} className="text-accent-red" />
                        <h4 className="text-body-sm-strong text-on-dark">Probable Root Cause</h4>
                      </div>
                      <p className="text-body-sm text-body">{result.probable_root_cause}</p>
                    </Card>
                    <Card variant="surface" hover={false}>
                      <div className="flex items-center gap-2 mb-3">
                        <CheckCircle2 size={14} className="text-accent-green" />
                        <h4 className="text-body-sm-strong text-on-dark">Recommended Fix</h4>
                      </div>
                      <p className="text-body-sm text-body">{result.recommended_fix}</p>
                    </Card>
                  </div>

                  {/* Reasoning */}
                  <Card variant="surface" hover={false}>
                    <h4 className="text-body-sm-strong text-on-dark mb-2">Reasoning</h4>
                    <p className="text-body-sm text-body leading-relaxed">{result.reasoning}</p>
                  </Card>

                  {/* Next steps */}
                  {result.next_steps?.length > 0 && (
                    <Card variant="surface" hover={false}>
                      <h4 className="text-body-sm-strong text-on-dark mb-3">Next Steps</h4>
                      <ul className="space-y-2">
                        {result.next_steps.map((step, i) => (
                          <li key={i} className="flex items-start gap-2.5">
                            <div className="w-5 h-5 rounded-full bg-surface-card border border-hairline flex items-center justify-center shrink-0 mt-0.5">
                              <span className="text-caption-sm text-mute">{i + 1}</span>
                            </div>
                            <span className="text-body-sm text-body">{step}</span>
                          </li>
                        ))}
                      </ul>
                    </Card>
                  )}

                  {/* Graph observations */}
                  {result.graph_context_used && result.graph_observations?.length > 0 && (
                    <Card variant="elevated" hover={false}>
                      <div className="flex items-center gap-2 mb-3">
                        <GitFork size={14} className="text-mute" />
                        <h4 className="text-body-sm-strong text-on-dark">Graph Observations</h4>
                      </div>
                      <ul className="space-y-1.5">
                        {result.graph_observations.map((obs, i) => (
                          <li key={i} className="text-body-sm text-mute flex items-start gap-2">
                            <span className="text-stone mt-0.5">•</span>
                            {obs}
                          </li>
                        ))}
                      </ul>
                    </Card>
                  )}

                  {/* Supporting entries */}
                  {result.supporting_entries?.length > 0 && (
                    <Card variant="elevated" hover={false}>
                      <h4 className="text-body-sm-strong text-on-dark mb-3">Supporting Evidence</h4>
                      <div className="space-y-2">
                        {result.supporting_entries.map((e) => (
                          <button
                            key={e.id}
                            onClick={() => navigate(`/knowledge/${e.id}`)}
                            className="w-full text-left flex items-start gap-3 p-2.5 rounded-sm hover:bg-surface-card transition-colors duration-100 cursor-pointer"
                          >
                            <div className="w-8 h-8 rounded-md bg-surface-card border border-hairline flex items-center justify-center shrink-0">
                              <Bug size={14} className="text-accent-blue" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <span className="text-body-sm text-on-dark block truncate">{e.title}</span>
                              <span className="text-caption-sm text-mute">
                                {(e.similarity_score * 100).toFixed(0)}% relevance
                              </span>
                            </div>
                            <ArrowRight size={12} className="text-stone mt-2 shrink-0" />
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
