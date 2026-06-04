import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Lightbulb, Send, Loader2, CheckCircle2, AlertTriangle,
  ArrowRight, Bug, GitFork, Plus, MessageSquare, User, Bot,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';
import PillTab from '../components/PillTab';
import { explainDebug, chatDebug } from '../lib/api';

export default function ExplainPage() {
  const navigate = useNavigate();
  const [rawInput, setRawInput] = useState('');
  const [topK, setTopK] = useState(3);
  const [includeGraph, setIncludeGraph] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Conversational RAG states
  const [activeTab, setActiveTab] = useState('Report');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);

  const chatEndRef = useRef(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, chatLoading]);

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

      // Prepopulate the chat history
      const initialReportMarkdown =
        `### AI Debug Explanation Summary\n\n` +
        `**Confidence**: ${(data.confidence * 100).toFixed(0)}%\n\n` +
        `#### Summary\n${data.summary}\n\n` +
        `#### Probable Root Cause\n${data.probable_root_cause}\n\n` +
        `#### Recommended Fix\n${data.recommended_fix}\n\n` +
        `#### Reasoning\n${data.reasoning}\n\n` +
        (data.next_steps?.length > 0
          ? `#### Next Steps\n${data.next_steps.map((s, i) => `${i + 1}. ${s}`).join('\n')}\n`
          : '');

      setChatMessages([
        { role: 'user', content: rawInput },
        { role: 'assistant', content: initialReportMarkdown }
      ]);
      setActiveTab('Report');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = { role: 'user', content: chatInput.trim() };
    const updatedMessages = [...chatMessages, userMessage];

    setChatMessages(updatedMessages);
    setChatInput('');
    setChatLoading(true);
    setChatError(null);

    // Build the retrieval context string to send to the chat endpoint
    const retrievalLines = [];
    if (result.supporting_entries?.length > 0) {
      retrievalLines.push("Retrieved Similar Entries:");
      result.supporting_entries.forEach(source => {
        retrievalLines.push(
          `Title: ${source.title}`,
          `ID: ${source.id}`,
          `Similarity: ${source.similarity_score}`,
          `Root Cause: ${source.root_cause}`,
          `Fix: ${source.fix}`,
          ""
        );
      });
    }
    if (result.graph_observations?.length > 0) {
      retrievalLines.push("Graph Observations:");
      retrievalLines.push(...result.graph_observations);
    }
    const retrievalContext = retrievalLines.join('\n').trim();

    try {
      const payload = updatedMessages.map(m => ({
        role: m.role,
        content: m.content
      }));

      const response = await chatDebug(payload, retrievalContext);
      setChatMessages(prev => [...prev, { role: 'assistant', content: response.reply }]);
    } catch (err) {
      setChatError(err.message);
    } finally {
      setChatLoading(false);
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
                  setChatMessages([]);
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
                <Card variant="elevated" hover={false} className="h-[650px] flex flex-col p-0 overflow-hidden">
                  {/* Workspace Tab Header */}
                  <div className="flex items-center justify-between px-6 py-4 border-b border-hairline bg-surface shrink-0">
                    <PillTab
                      tabs={['Report', 'Chat']}
                      activeTab={activeTab}
                      onTabChange={setActiveTab}
                    />
                    <Badge variant="success">
                      {((result.confidence || 0) * 100).toFixed(0)}% confidence
                    </Badge>
                  </div>

                  {/* Tab Contents */}
                  <div className="flex-1 overflow-y-auto min-h-0 bg-surface">
                    {activeTab === 'Report' ? (
                      <div className="p-6 space-y-6">
                        {/* Summary */}
                        <div>
                          <div className="flex items-center gap-2 mb-3">
                            <Lightbulb size={16} className="text-accent-blue" />
                            <h4 className="text-body-sm-strong text-on-dark">Explanation</h4>
                          </div>
                          <p className="text-body-md text-body leading-relaxed">{result.summary}</p>
                        </div>

                        {/* Root cause & Fix */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-hairline-soft pt-6">
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <AlertTriangle size={14} className="text-accent-red" />
                              <h4 className="text-body-sm-strong text-on-dark">Probable Root Cause</h4>
                            </div>
                            <p className="text-body-sm text-body leading-relaxed">{result.probable_root_cause}</p>
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <CheckCircle2 size={14} className="text-accent-green" />
                              <h4 className="text-body-sm-strong text-on-dark">Recommended Fix</h4>
                            </div>
                            <p className="text-body-sm text-body leading-relaxed">{result.recommended_fix}</p>
                          </div>
                        </div>

                        {/* Reasoning */}
                        <div className="border-t border-hairline-soft pt-6">
                          <h4 className="text-body-sm-strong text-on-dark mb-3">Reasoning</h4>
                          <p className="text-body-sm text-body leading-relaxed">{result.reasoning}</p>
                        </div>

                        {/* Next steps */}
                        {result.next_steps?.length > 0 && (
                          <div className="border-t border-hairline-soft pt-6">
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
                          </div>
                        )}

                        {/* Graph observations */}
                        {result.graph_context_used && result.graph_observations?.length > 0 && (
                          <div className="border-t border-hairline-soft pt-6">
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
                          </div>
                        )}

                        {/* Supporting entries */}
                        {result.supporting_entries?.length > 0 && (
                          <div className="border-t border-hairline-soft pt-6">
                            <h4 className="text-body-sm-strong text-on-dark mb-3">Supporting Evidence</h4>
                            <div className="space-y-2">
                              {result.supporting_entries.map((e) => (
                                <button
                                  key={e.id}
                                  onClick={() => navigate(`/knowledge/${e.id}`)}
                                  className="w-full text-left flex items-start gap-3 p-2.5 rounded-sm hover:bg-surface-card transition-colors duration-100 cursor-pointer border border-hairline"
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
                          </div>
                        )}
                      </div>
                    ) : (
                      /* Chat Tab Content */
                      <div className="flex flex-col h-full">
                        {/* Chat messages feed */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0">
                          {chatMessages.map((msg, i) => {
                            const isUser = msg.role === 'user';
                            return (
                              <div key={i} className={`flex gap-3 max-w-[85%] ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
                                {/* Avatar */}
                                <div className={`w-8 h-8 rounded-md border border-hairline flex items-center justify-center shrink-0 ${isUser ? 'bg-surface-elevated' : 'bg-accent-blue-soft'}`}>
                                  {isUser ? <User size={14} className="text-mute" /> : <Bot size={14} className="text-accent-blue" />}
                                </div>
                                {/* Bubble */}
                                <div className={`p-4 rounded-lg border text-body-sm leading-relaxed ${isUser ? 'bg-surface-card border-hairline text-on-dark' : 'bg-surface-elevated border-hairline text-body'}`}>
                                  <div className="markdown-content font-sans">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                      {msg.content}
                                    </ReactMarkdown>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                          {chatLoading && (
                            <div className="flex gap-3 max-w-[85%] mr-auto">
                              <div className="w-8 h-8 rounded-md border border-hairline bg-accent-blue-soft flex items-center justify-center shrink-0">
                                <Bot size={14} className="text-accent-blue" />
                              </div>
                              <div className="p-4 rounded-lg border border-hairline bg-surface-elevated text-body flex items-center gap-2">
                                <Loader2 size={14} className="animate-spin text-accent-blue" />
                                <span className="text-caption-sm text-mute">Synthesizing reply...</span>
                              </div>
                            </div>
                          )}
                          {chatError && (
                            <div className="p-3 bg-accent-red-soft rounded-md text-body-sm text-accent-red">
                              Error: {chatError}
                            </div>
                          )}
                          <div ref={chatEndRef} />
                        </div>

                        {/* Chat input bar */}
                        <form onSubmit={handleChatSubmit} className="flex gap-2 p-3 border-t border-hairline bg-surface shrink-0">
                          <textarea
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleChatSubmit(e);
                              }
                            }}
                            placeholder="Ask a follow-up question..."
                            rows={1}
                            className="
                              flex-1 px-4 py-2.5
                              bg-surface-elevated text-on-dark
                              border border-hairline rounded-md
                              text-body-sm font-sans
                              placeholder:text-stone
                              outline-none resize-none
                              focus:border-hairline-strong
                              transition-colors duration-150
                            "
                          />
                          <Button type="submit" variant={chatInput.trim() && !chatLoading ? 'primary' : 'disabled'} className="shrink-0 h-10 w-10 flex items-center justify-center p-0 rounded-md">
                            <Send size={14} />
                          </Button>
                        </form>
                      </div>
                    )}
                  </div>
                </Card>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
