import { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Search, BookOpen, Plus, BarChart3,
  GitFork, Lightbulb, Menu, X, Activity,
} from 'lucide-react';
import Button from './Button';
import { healthCheck } from '../lib/api';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/knowledge', label: 'Knowledge', icon: BookOpen },
  { to: '/add', label: 'Add', icon: Plus },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/graph', label: 'Graph', icon: GitFork },
  { to: '/explain', label: 'Explain', icon: Lightbulb },
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [isHealthy, setIsHealthy] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    healthCheck()
      .then(() => setIsHealthy(true))
      .catch(() => setIsHealthy(false));

    const interval = setInterval(() => {
      healthCheck()
        .then(() => setIsHealthy(true))
        .catch(() => setIsHealthy(false));
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="sticky top-0 z-50 bg-canvas/95 backdrop-blur-sm border-b border-hairline h-14">
      <div className="max-w-[1240px] mx-auto px-4 md:px-6 h-full flex items-center">
        {/* Wordmark */}
        <NavLink to="/" className="flex items-center gap-2.5 mr-8 shrink-0">
          <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center">
            <span className="text-on-primary font-semibold text-xs">DIS</span>
          </div>
          <span className="text-body-sm-strong text-on-dark hidden sm:inline">
            Debug Intelligence
          </span>
        </NavLink>

        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-1 flex-1 justify-center">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-body-sm transition-colors duration-150 ${
                  isActive
                    ? 'text-on-dark bg-surface-elevated'
                    : 'text-mute hover:text-on-dark'
                }`
              }
            >
              <Icon size={14} />
              {label}
            </NavLink>
          ))}
        </div>

        {/* Right cluster */}
        <div className="flex items-center gap-3 ml-auto">
          {/* Health indicator */}
          <div className="flex items-center gap-1.5" title={isHealthy === null ? 'Checking...' : isHealthy ? 'API Connected' : 'API Offline'}>
            <Activity
              size={14}
              className={
                isHealthy === null
                  ? 'text-mute'
                  : isHealthy
                  ? 'text-accent-green'
                  : 'text-accent-red'
              }
            />
            <span className="text-caption-sm text-mute hidden md:inline">
              {isHealthy === null ? '...' : isHealthy ? 'Online' : 'Offline'}
            </span>
          </div>

          <Button size="sm" onClick={() => navigate('/add')} className="hidden sm:inline-flex">
            Add Incident
          </Button>

          {/* Mobile hamburger */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="lg:hidden text-on-dark p-1.5 cursor-pointer"
            aria-label="Toggle menu"
          >
            {isOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {isOpen && (
        <div className="lg:hidden absolute top-14 inset-x-0 bg-canvas border-b border-hairline z-50">
          <div className="flex flex-col py-2 px-4">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2.5 rounded-md text-body-sm transition-colors duration-150 ${
                    isActive
                      ? 'text-on-dark bg-surface-elevated'
                      : 'text-mute hover:text-on-dark'
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
