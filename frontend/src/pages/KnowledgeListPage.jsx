import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Bug } from 'lucide-react';
import PillTab from '../components/PillTab';
import Card from '../components/Card';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';
import { listKnowledge } from '../lib/api';

const categoryTabs = ['All', 'frontend', 'backend', 'infra', 'uncategorized'];

export default function KnowledgeListPage() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState('All');

  useEffect(() => {
    setLoading(true);
    const cat = activeCategory !== 'All' ? activeCategory : null;
    listKnowledge(cat)
      .then((data) => setEntries(data.entries || []))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [activeCategory]);

  return (
    <div className="page-enter max-w-[1240px] mx-auto px-6 md:px-12 py-12 md:py-16">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-display-lg mb-3">Knowledge Base</h1>
        <p className="text-body-lg text-mute">
          Browse all structured debugging knowledge entries.
        </p>
      </div>

      {/* Category filter */}
      <PillTab
        tabs={categoryTabs}
        activeTab={activeCategory}
        onTabChange={setActiveCategory}
        className="mb-8"
      />

      {/* Entry list */}
      {loading ? (
        <LoadingSpinner className="py-24" />
      ) : entries.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No entries yet"
          description="Add your first debugging incident to start building the knowledge base."
        />
      ) : (
        <div className="flex flex-col gap-3">
          {entries.map((entry) => (
            <Card
              key={entry.id}
              variant="store"
              onClick={() => navigate(`/knowledge/${entry.id}`)}
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-md bg-surface-card border border-hairline flex items-center justify-center shrink-0">
                  <Bug size={18} className="text-accent-blue" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-body-strong text-on-dark">{entry.title}</h3>
                    <Badge variant="success">
                      {((entry.confidence || 0) * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2.5">
                    <Badge variant="pro">{entry.category}</Badge>
                    {entry.tech_stack?.slice(0, 3).map((tech) => (
                      <Badge key={tech} variant="info">{tech}</Badge>
                    ))}
                    {entry.tags?.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="neutral">{tag}</Badge>
                    ))}
                  </div>
                  {entry.related_ids?.length > 0 && (
                    <p className="text-caption-sm text-stone mt-2">
                      {entry.related_ids.length} related entr{entry.related_ids.length === 1 ? 'y' : 'ies'}
                    </p>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
