import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import DashboardPage from './pages/DashboardPage';
import SearchPage from './pages/SearchPage';
import KnowledgeListPage from './pages/KnowledgeListPage';
import KnowledgeDetailPage from './pages/KnowledgeDetailPage';
import AddEntryPage from './pages/AddEntryPage';
import AnalyticsPage from './pages/AnalyticsPage';
import GraphPage from './pages/GraphPage';
import ExplainPage from './pages/ExplainPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-canvas">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/knowledge" element={<KnowledgeListPage />} />
            <Route path="/knowledge/:id" element={<KnowledgeDetailPage />} />
            <Route path="/add" element={<AddEntryPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/explain" element={<ExplainPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
