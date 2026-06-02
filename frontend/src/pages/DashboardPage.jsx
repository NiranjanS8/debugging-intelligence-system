import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Database, TrendingUp, Layers, Zap, ArrowRight, Bug,
} from 'lucide-react';
import HeroStripe from '../components/HeroStripe';
import CommandPaletteCard from '../components/CommandPaletteCard';
import Card from '../components/Card';
import Badge from '../components/Badge';
import SearchBar from '../components/SearchBar';
import LoadingSpinner from '../components/LoadingSpinner';
import { getAnalyticsSummary, listKnowledge } from '../lib/api';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [entries, setEntries] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getAnalyticsSummary().catch(() => null),
      listKnowledge().catch(() => ({ entries: [] })),
    ]).then(([sum, know]) => {
      setSummary(sum);
      setEntries(know?.entries || []);
      setLoading(false);
    });
  }, []);

  const stats = summary
    ? [
        { label: 'Total Entries', value: summary.total_entries, icon: Database, variant: 'info' },
        { label: 'Avg Confidence', value: `${(summary.avg_confidence * 100).toFixed(0)}%`, icon: TrendingUp, variant: 'success' },
        { label: 'Categories', value: Object.keys(summary.total_categories).length, icon: Layers, variant: 'warning' },
        { label: 'Tech Stacks', value: Object.keys(summary.tech_stack_distribution).length, icon: Zap, variant: 'pro' },
      ]
    : [];

  return (
    <div className="page-enter">
      {/* Hero */}
      <HeroStripe
        title="Debug Intelligence System"
        subtitle="Turn raw debugging sessions into searchable, reusable knowledge. Semantic search, AI-powered explanations, and pattern detection, all in one place."
        ctaText="Add Incident"
        onCtaClick={() => navigate('/add')}
      >
        <CommandPaletteCard entries={entries.slice(0, 5)} />
      </HeroStripe>

      <div className="max-w-[1240px] mx-auto px-6 md:px-12">
        {/* Quick search */}
        <section className="py-12 md:py-16">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSubmit={(q) => navigate(`/search?q=${encodeURIComponent(q)}`)}
            placeholder="Quick search your knowledge base..."
            className="max-w-2xl mx-auto"
          />
        </section>

        {/* Stats */}
        {loading ? (
          <LoadingSpinner className="py-16" />
        ) : stats.length > 0 ? (
          <section className="pb-16 md:pb-(--spacing-section)">
            <h2 className="text-heading-md mb-6">Knowledge Base Overview</h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {stats.map((s) => (
                <Card key={s.label} variant="surface" hover={false}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-9 h-9 rounded-md bg-surface-card border border-hairline flex items-center justify-center">
                      <s.icon size={18} className="text-mute" />
                    </div>
                    <Badge variant={s.variant}>{s.label}</Badge>
                  </div>
                  <p className="text-display-lg text-ink leading-none">{s.value}</p>
                </Card>
              ))}
            </div>
          </section>
        ) : null}

        {/* Top root causes */}
        {summary?.most_common_root_causes?.length > 0 && (
          <section className="pb-16 md:pb-(--spacing-section)">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-heading-md">Top Root Causes</h2>
              <button
                onClick={() => navigate('/analytics')}
                className="text-body-sm text-mute hover:text-on-dark transition-colors duration-150 flex items-center gap-1 cursor-pointer"
              >
                View analytics <ArrowRight size={14} />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {summary.most_common_root_causes.slice(0, 6).map((cause, i) => (
                <Card key={i} variant="elevated" hover={false}>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-md bg-surface-card border border-hairline flex items-center justify-center shrink-0 mt-0.5">
                      <Bug size={14} className="text-mute" />
                    </div>
                    <p className="text-body-sm text-body leading-relaxed">{cause}</p>
                  </div>
                </Card>
              ))}
            </div>
          </section>
        )}

        {/* Recent entries */}
        {entries.length > 0 && (
          <section className="pb-16 md:pb-(--spacing-section)">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-heading-md">Recent Entries</h2>
              <button
                onClick={() => navigate('/knowledge')}
                className="text-body-sm text-mute hover:text-on-dark transition-colors duration-150 flex items-center gap-1 cursor-pointer"
              >
                View all <ArrowRight size={14} />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {entries.slice(0, 6).map((entry) => (
                <Card
                  key={entry.id}
                  variant="store"
                  onClick={() => navigate(`/knowledge/${entry.id}`)}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-md bg-surface-card border border-hairline flex items-center justify-center shrink-0">
                      <Bug size={16} className="text-accent-blue" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-body-strong text-on-dark truncate">{entry.title}</h3>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        <Badge variant="pro">{entry.category}</Badge>
                        {entry.tags?.slice(0, 2).map((tag) => (
                          <Badge key={tag} variant="neutral">{tag}</Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
