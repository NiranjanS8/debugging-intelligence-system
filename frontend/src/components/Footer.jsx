import { NavLink } from 'react-router-dom';

const columns = [
  {
    title: 'Product',
    links: [
      { label: 'Dashboard', to: '/' },
      { label: 'Search', to: '/search' },
      { label: 'Add Incident', to: '/add' },
      { label: 'Explain', to: '/explain' },
    ],
  },
  {
    title: 'Intelligence',
    links: [
      { label: 'Knowledge Base', to: '/knowledge' },
      { label: 'Analytics', to: '/analytics' },
      { label: 'Graph Explorer', to: '/graph' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'API Docs', href: 'http://localhost:8000/docs' },
      { label: 'ReDoc', href: 'http://localhost:8000/redoc' },
      { label: 'Health', href: 'http://localhost:8000/health' },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-hairline bg-canvas">
      <div className="max-w-[1240px] mx-auto px-6 md:px-12 py-12 md:py-16">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-8 md:gap-12">
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="text-body-sm-strong text-on-dark mb-4">{col.title}</h4>
              <ul className="flex flex-col gap-2.5">
                {col.links.map((link) => (
                  <li key={link.label}>
                    {link.to ? (
                      <NavLink
                        to={link.to}
                        className="text-body-sm text-body hover:text-on-dark transition-colors duration-150"
                      >
                        {link.label}
                      </NavLink>
                    ) : (
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-body-sm text-body hover:text-on-dark transition-colors duration-150"
                      >
                        {link.label} ↗
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom row */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-12 pt-6 border-t border-hairline">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-sm bg-primary flex items-center justify-center">
              <span className="text-on-primary font-semibold text-[10px]">DIS</span>
            </div>
            <span className="text-caption-sm text-mute">
              Debugging Intelligence System
            </span>
          </div>
          <span className="text-caption-sm text-stone">
            v0.1.0 · Built with FastAPI + React
          </span>
        </div>
      </div>
    </footer>
  );
}
