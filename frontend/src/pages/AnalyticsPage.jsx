import { useState, useEffect } from 'react';
import { BarChart3, Layers, Tag, Cpu, RefreshCw, Loader2 } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import PillTab from '../components/PillTab';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import {
  getAnalyticsSummary,
  getFailurePatterns,
  clusterEntries,
} from '../lib/api';

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [clusters, setClusters] = useState(null);
  const [loading, setLoading] = useState(true);
  const [clusterLoading, setClusterLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      getAnalyticsSummary().catch(() => null),
      getFailurePatterns(10).catch(() => null),
    ]).then(([sum, pat]) => {
      setSummary(sum);
      setPatterns(pat);
      setLoading(false);
    });
  }, []);

  const handleCluster = async () => {
    setClusterLoading(true);
    try {
      const data = await clusterEntries();
      setClusters(data);
    } catch (err) {
      console.error('Clustering failed:', err);
    } finally {
      setClusterLoading(false);
    }
  };

  if (loading) return <LoadingSpinner className="py-32" />;

  const renderBarChart = (items, color) => {
    if (!items || items.length === 0) return null;
    const maxCount = Math.max(...items.map((i) => i.count));
    return (
      <div className="space-y-2.5">
        {items.map((item) => (
          <div key={item.name} className="group">
            <div className="flex items-center justify-between mb-1">
              <span className="text-body-sm text-body truncate pr-4">{item.name}</span>
              <span className="text-caption-sm text-mute shrink-0">
                {item.count} ({item.percentage.toFixed(1)}%)
              </span>
            </div>
            <div className="h-1.5 bg-surface-card rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${color}`}
                style={{ width: `${(item.count / maxCount) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="page-enter max-w-[1240px] mx-auto px-6 md:px-12 py-12 md:py-16">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-display-lg mb-3">Analytics</h1>
        <p className="text-body-lg text-mute">
          Failure patterns, distributions, and root-cause clustering.
        </p>
      </div>

      {!summary ? (
        <EmptyState
          icon={BarChart3}
          title="No analytics data"
          description="Add debugging entries to generate analytics."
        />
      ) : (
        <>
          {/* Summary cards */}
          <section className="mb-12">
            <h2 className="text-heading-md mb-4">Overview</h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <Card variant="surface" hover={false}>
                <p className="text-caption-sm text-mute mb-1">Total Entries</p>
                <p className="text-heading-xl text-ink">{summary.total_entries}</p>
              </Card>
              <Card variant="surface" hover={false}>
                <p className="text-caption-sm text-mute mb-1">Avg Confidence</p>
                <p className="text-heading-xl text-ink">{(summary.avg_confidence * 100).toFixed(0)}%</p>
              </Card>
              <Card variant="surface" hover={false}>
                <p className="text-caption-sm text-mute mb-1">Categories</p>
                <p className="text-heading-xl text-ink">{Object.keys(summary.total_categories).length}</p>
              </Card>
              <Card variant="surface" hover={false}>
                <p className="text-caption-sm text-mute mb-1">Tech Stacks</p>
                <p className="text-heading-xl text-ink">{Object.keys(summary.tech_stack_distribution).length}</p>
              </Card>
            </div>
          </section>

          {/* Category distribution */}
          {Object.keys(summary.total_categories).length > 0 && (
            <section className="mb-12">
              <h2 className="text-heading-md mb-4">Categories</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(summary.total_categories).map(([cat, count]) => (
                  <Card key={cat} variant="elevated" hover={false}>
                    <div className="flex items-center justify-between">
                      <Badge variant="pro">{cat}</Badge>
                      <span className="text-heading-sm text-ink">{count}</span>
                    </div>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Tech stack & Tag distribution */}
          <section className="mb-12">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.keys(summary.tech_stack_distribution).length > 0 && (
                <Card variant="surface" hover={false}>
                  <div className="flex items-center gap-2 mb-4">
                    <Cpu size={16} className="text-mute" />
                    <h3 className="text-body-strong text-on-dark">Tech Stack</h3>
                  </div>
                  <div className="space-y-2">
                    {Object.entries(summary.tech_stack_distribution)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 10)
                      .map(([tech, count]) => {
                        const maxVal = Math.max(...Object.values(summary.tech_stack_distribution));
                        return (
                          <div key={tech}>
                            <div className="flex justify-between mb-0.5">
                              <span className="text-body-sm text-body">{tech}</span>
                              <span className="text-caption-sm text-mute">{count}</span>
                            </div>
                            <div className="h-1 bg-surface-card rounded-full overflow-hidden">
                              <div
                                className="h-full bg-accent-blue rounded-full"
                                style={{ width: `${(count / maxVal) * 100}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </Card>
              )}

              {Object.keys(summary.tag_distribution).length > 0 && (
                <Card variant="surface" hover={false}>
                  <div className="flex items-center gap-2 mb-4">
                    <Tag size={16} className="text-mute" />
                    <h3 className="text-body-strong text-on-dark">Tags</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(summary.tag_distribution)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 20)
                      .map(([tag, count]) => (
                        <Badge key={tag} variant="neutral">
                          {tag} · {count}
                        </Badge>
                      ))}
                  </div>
                </Card>
              )}
            </div>
          </section>

          {/* Failure patterns */}
          {patterns && (
            <section className="mb-12">
              <h2 className="text-heading-md mb-4">Failure Patterns</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {patterns.top_root_causes?.length > 0 && (
                  <Card variant="surface" hover={false}>
                    <h3 className="text-body-sm-strong text-on-dark mb-4">Top Root Causes</h3>
                    {renderBarChart(patterns.top_root_causes, 'bg-accent-red')}
                  </Card>
                )}
                {patterns.top_tags?.length > 0 && (
                  <Card variant="surface" hover={false}>
                    <h3 className="text-body-sm-strong text-on-dark mb-4">Top Tags</h3>
                    {renderBarChart(patterns.top_tags, 'bg-accent-yellow')}
                  </Card>
                )}
                {patterns.top_tech_stack?.length > 0 && (
                  <Card variant="surface" hover={false}>
                    <h3 className="text-body-sm-strong text-on-dark mb-4">Top Tech Stacks</h3>
                    {renderBarChart(patterns.top_tech_stack, 'bg-accent-green')}
                  </Card>
                )}
              </div>
            </section>
          )}

          {/* Clustering */}
          <section className="mb-12">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-heading-md">Root-Cause Clustering</h2>
              <Button
                variant="tertiary"
                size="sm"
                onClick={handleCluster}
                disabled={clusterLoading}
              >
                {clusterLoading ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Clustering...
                  </>
                ) : (
                  <>
                    <RefreshCw size={14} />
                    Run Clustering
                  </>
                )}
              </Button>
            </div>

            {clusters ? (
              clusters.clusters?.length > 0 ? (
                <div className="space-y-4">
                  <p className="text-body-sm text-mute">
                    {clusters.total_clusters} cluster{clusters.total_clusters !== 1 ? 's' : ''} found
                    from {clusters.total_entries} entries
                    {clusters.noise_entries > 0 && ` (${clusters.noise_entries} noise)`}
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {clusters.clusters.map((c) => (
                      <Card key={c.cluster_id} variant="elevated" hover={false}>
                        <div className="flex items-start justify-between mb-3">
                          <h4 className="text-body-strong text-on-dark">{c.label}</h4>
                          <Badge variant="info">{c.size} entries</Badge>
                        </div>
                        {c.entry_titles?.length > 0 && (
                          <ul className="text-body-sm text-mute space-y-1 mb-3">
                            {c.entry_titles.slice(0, 4).map((t, i) => (
                              <li key={i} className="truncate">• {t}</li>
                            ))}
                            {c.entry_titles.length > 4 && (
                              <li className="text-stone">...and {c.entry_titles.length - 4} more</li>
                            )}
                          </ul>
                        )}
                        <div className="flex flex-wrap gap-1">
                          {c.common_tags?.slice(0, 4).map((t) => (
                            <Badge key={t} variant="neutral">{t}</Badge>
                          ))}
                          {c.common_tech_stack?.slice(0, 3).map((t) => (
                            <Badge key={t} variant="info">{t}</Badge>
                          ))}
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={Layers}
                  title="No clusters formed"
                  description="Not enough entries to form meaningful clusters yet."
                />
              )
            ) : (
              <Card variant="elevated" hover={false} className="text-center py-12">
                <p className="text-body-sm text-mute">
                  Click "Run Clustering" to analyze root-cause groups using embedding similarity.
                </p>
              </Card>
            )}
          </section>
        </>
      )}
    </div>
  );
}
