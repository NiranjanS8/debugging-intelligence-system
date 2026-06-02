import { useState, useEffect, useCallback, useRef } from 'react';
import { GitFork, Search } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import TextInput from '../components/TextInput';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { getGraphSummary, getGraphEntry } from '../lib/api';

// Node color mapping by label type
const nodeColors = {
  Bug: '#57c1ff',       // accent-blue
  RootCause: '#ff6161', // accent-red
  Tech: '#59d499',      // accent-green
  Tag: '#ffc533',       // accent-yellow
  Symptom: '#9c9c9d',   // mute
};

export default function GraphPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [entryId, setEntryId] = useState('');
  const [neighborhood, setNeighborhood] = useState(null);
  const [neighborhoodLoading, setNeighborhoodLoading] = useState(false);
  const [graphError, setGraphError] = useState(null);
  const graphRef = useRef(null);
  const [ForceGraph, setForceGraph] = useState(null);

  useEffect(() => {
    getGraphSummary()
      .then(setSummary)
      .catch(() => setSummary({ graph_enabled: false }))
      .finally(() => setLoading(false));

    // Dynamically import react-force-graph-2d (it uses canvas, may not work in SSR)
    import('react-force-graph-2d')
      .then((mod) => setForceGraph(() => mod.default))
      .catch(() => {});
  }, []);

  const lookupEntry = async () => {
    if (!entryId.trim()) return;
    setNeighborhoodLoading(true);
    setGraphError(null);
    try {
      const data = await getGraphEntry(entryId.trim());
      setNeighborhood(data);
    } catch (err) {
      setGraphError(err.message);
      setNeighborhood(null);
    } finally {
      setNeighborhoodLoading(false);
    }
  };

  // Transform neighborhood to force-graph format
  const graphData = neighborhood
    ? {
        nodes: neighborhood.nodes.map((n) => ({
          id: n.node_id,
          label: n.properties?.name || n.properties?.title || n.node_id.slice(0, 16),
          group: n.label,
          color: nodeColors[n.label] || '#6a6b6c',
        })),
        links: neighborhood.edges.map((e) => ({
          source: e.source,
          target: e.target,
          label: e.relationship,
        })),
      }
    : null;

  const nodeCanvasObject = useCallback(
    (node, ctx, globalScale) => {
      const label = node.label;
      const fontSize = 11 / globalScale;
      ctx.font = `500 ${fontSize}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // Node circle
      const r = 6;
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
      ctx.fillStyle = node.color;
      ctx.fill();

      // Label below
      ctx.fillStyle = '#cdcdcd';
      ctx.fillText(label, node.x, node.y + r + fontSize);
    },
    []
  );

  if (loading) return <LoadingSpinner className="py-32" />;

  return (
    <div className="page-enter max-w-[1240px] mx-auto px-6 md:px-12 py-12 md:py-16">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-display-lg mb-3">Graph Explorer</h1>
        <p className="text-body-lg text-mute">
          Explore the Neo4j knowledge graph: bugs, root causes, technologies, and relationships.
        </p>
      </div>

      {!summary?.graph_enabled ? (
        <EmptyState
          icon={GitFork}
          title="Graph not enabled"
          description="Neo4j graph features are disabled. Set NEO4J_ENABLED=true in your .env to enable the knowledge graph."
        />
      ) : (
        <>
          {/* Summary stats */}
          <section className="mb-10">
            <h2 className="text-heading-md mb-4">Graph Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {[
                { label: 'Bugs', value: summary.total_bugs, color: 'info' },
                { label: 'Root Causes', value: summary.total_root_causes, color: 'error' },
                { label: 'Technologies', value: summary.total_technologies, color: 'success' },
                { label: 'Symptoms', value: summary.total_symptoms, color: 'neutral' },
                { label: 'Tags', value: summary.total_tags, color: 'warning' },
                { label: 'Similarity', value: summary.total_similarity_edges, color: 'pro' },
              ].map((s) => (
                <Card key={s.label} variant="surface" hover={false}>
                  <Badge variant={s.color} className="mb-2">{s.label}</Badge>
                  <p className="text-heading-lg text-ink">{s.value}</p>
                </Card>
              ))}
            </div>
          </section>

          {/* Entry lookup */}
          <section className="mb-10">
            <h2 className="text-heading-md mb-4">Entry Neighborhood</h2>
            <div className="flex gap-3 mb-4">
              <TextInput
                value={entryId}
                onChange={(e) => setEntryId(e.target.value)}
                placeholder="Enter an entry ID..."
                className="flex-1"
              />
              <Button variant="tertiary" onClick={lookupEntry} disabled={neighborhoodLoading}>
                <Search size={14} />
                Lookup
              </Button>
            </div>

            {graphError && (
              <div className="p-3 bg-accent-red-soft rounded-md text-body-sm text-accent-red mb-4">
                {graphError}
              </div>
            )}

            {/* Color legend */}
            <div className="flex flex-wrap gap-4 mb-6">
              {Object.entries(nodeColors).map(([label, color]) => (
                <div key={label} className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-caption-sm text-mute">{label}</span>
                </div>
              ))}
            </div>

            {neighborhoodLoading ? (
              <LoadingSpinner className="py-16" />
            ) : graphData ? (
              <Card variant="surface" hover={false} className="overflow-hidden p-0">
                <div className="p-3 border-b border-hairline flex items-center justify-between">
                  <span className="text-body-sm-strong text-on-dark">
                    {neighborhood.entry_id}
                  </span>
                  <span className="text-caption-sm text-mute">
                    {neighborhood.total_nodes} nodes · {neighborhood.total_edges} edges
                  </span>
                </div>
                <div className="h-[500px] bg-canvas">
                  {ForceGraph ? (
                    <ForceGraph
                      ref={graphRef}
                      graphData={graphData}
                      nodeCanvasObject={nodeCanvasObject}
                      linkColor={() => '#242728'}
                      linkDirectionalArrowLength={4}
                      linkDirectionalArrowRelPos={1}
                      linkLabel="label"
                      backgroundColor="#07080a"
                      width={undefined}
                      height={500}
                      cooldownTicks={100}
                    />
                  ) : (
                    <div className="h-full flex items-center justify-center text-body-sm text-mute">
                      Loading graph renderer...
                    </div>
                  )}
                </div>
              </Card>
            ) : (
              <Card variant="elevated" hover={false} className="text-center py-16">
                <p className="text-body-sm text-mute">
                  Enter a debug entry ID above to visualize its graph neighborhood.
                </p>
              </Card>
            )}
          </section>
        </>
      )}
    </div>
  );
}
