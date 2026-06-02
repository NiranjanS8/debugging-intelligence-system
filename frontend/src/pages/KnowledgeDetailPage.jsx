import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowLeft, Bug, ExternalLink } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { getKnowledgeEntry, getSimilar } from '../lib/api';

export default function KnowledgeDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getKnowledgeEntry(id),
      getSimilar(id, 5).catch(() => []),
    ])
      .then(([entryData, simData]) => {
        setData(entryData);
        setSimilar(Array.isArray(simData) ? simData : []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner className="py-32" />;
  if (error)
    return (
      <EmptyState
        icon={Bug}
        title="Entry not found"
        description={error}
      >
        <Button variant="secondary" onClick={() => navigate('/knowledge')}>
          Back to Knowledge Base
        </Button>
      </EmptyState>
    );

  const entry = data?.entry;
  const markdown = data?.markdown_content;

  if (!entry) return null;

  return (
    <div className="page-enter max-w-[1240px] mx-auto px-6 md:px-12 py-12 md:py-16">
      {/* Back link */}
      <button
        onClick={() => navigate('/knowledge')}
        className="flex items-center gap-1.5 text-body-sm text-mute hover:text-on-dark transition-colors duration-150 mb-6 cursor-pointer"
      >
        <ArrowLeft size={14} />
        Back to Knowledge Base
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2">
          {/* Header */}
          <Card variant="surface" hover={false} className="mb-6">
            <h1 className="text-heading-xl mb-4">{entry.title}</h1>

            <div className="flex flex-wrap gap-2 mb-6">
              <Badge variant="pro">{entry.category}</Badge>
              <Badge variant="success">
                {((entry.confidence || 0) * 100).toFixed(0)}% confidence
              </Badge>
              {entry.tech_stack?.map((tech) => (
                <Badge key={tech} variant="info">{tech}</Badge>
              ))}
              {entry.tags?.map((tag) => (
                <Badge key={tag} variant="neutral">{tag}</Badge>
              ))}
            </div>

            {/* Structured fields */}
            <div className="space-y-4">
              {entry.symptoms?.length > 0 && (
                <div>
                  <h3 className="text-body-sm-strong text-on-dark mb-1.5">Symptoms</h3>
                  <ul className="list-disc list-inside text-body-sm text-body space-y-1">
                    {entry.symptoms.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div>
                <h3 className="text-body-sm-strong text-on-dark mb-1.5">Root Cause</h3>
                <p className="text-body-sm text-body">{entry.root_cause}</p>
              </div>

              <div>
                <h3 className="text-body-sm-strong text-on-dark mb-1.5">Fix</h3>
                <p className="text-body-sm text-body">{entry.fix}</p>
              </div>
            </div>
          </Card>

          {/* Markdown content */}
          {markdown && (
            <Card variant="surface" hover={false}>
              <h2 className="text-heading-md mb-4">Knowledge Page</h2>
              <div className="markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {markdown}
                </ReactMarkdown>
              </div>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Metadata */}
          <Card variant="elevated" hover={false}>
            <h3 className="text-body-sm-strong text-on-dark mb-3">Details</h3>
            <dl className="space-y-2.5 text-body-sm">
              <div className="flex justify-between">
                <dt className="text-mute">ID</dt>
                <dd className="text-body font-mono text-caption-sm truncate max-w-[160px]">{entry.id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-mute">Category</dt>
                <dd className="text-body">{entry.category}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-mute">Updates</dt>
                <dd className="text-body">{entry.update_count || 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-mute">Reliability</dt>
                <dd className="text-body">
                  {((entry.similarity_reliability || 0) * 100).toFixed(0)}%
                </dd>
              </div>
              {entry.markdown_path && (
                <div className="flex justify-between">
                  <dt className="text-mute">File</dt>
                  <dd className="text-body truncate max-w-[160px]">{entry.markdown_path}</dd>
                </div>
              )}
            </dl>
          </Card>

          {/* Similar entries */}
          {similar.length > 0 && (
            <Card variant="elevated" hover={false}>
              <h3 className="text-body-sm-strong text-on-dark mb-3">Similar Entries</h3>
              <div className="space-y-2.5">
                {similar.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => navigate(`/knowledge/${s.id}`)}
                    className="w-full text-left p-2.5 rounded-sm hover:bg-surface-card transition-colors duration-100 cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-body-sm text-on-dark line-clamp-2">{s.title}</span>
                      <span className="text-caption-sm text-mute shrink-0">
                        {(s.similarity_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </Card>
          )}

          {/* Related IDs */}
          {entry.related_ids?.length > 0 && (
            <Card variant="elevated" hover={false}>
              <h3 className="text-body-sm-strong text-on-dark mb-3">Related</h3>
              <div className="flex flex-wrap gap-1.5">
                {entry.related_ids.map((rid) => (
                  <button
                    key={rid}
                    onClick={() => navigate(`/knowledge/${rid}`)}
                    className="flex items-center gap-1 text-caption-sm text-accent-blue hover:underline cursor-pointer"
                  >
                    <ExternalLink size={10} />
                    {rid.slice(0, 12)}…
                  </button>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
