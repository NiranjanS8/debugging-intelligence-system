import { Bug, Search, Terminal } from 'lucide-react';
import Keycap from './Keycap';

const mockRows = [
  { icon: <Bug size={16} className="text-accent-red" />, label: 'TypeError: Cannot read property of null', shortcut: '⏎' },
  { icon: <Terminal size={16} className="text-accent-green" />, label: 'CORS blocked by access-control-allow-origin', shortcut: null },
  { icon: <Bug size={16} className="text-accent-yellow" />, label: 'React useEffect cleanup memory leak', shortcut: null },
  { icon: <Search size={16} className="text-accent-blue" />, label: 'Docker container exits with code 137', shortcut: null },
  { icon: <Terminal size={16} className="text-accent-green" />, label: 'PostgreSQL connection pool exhausted', shortcut: null },
];

export default function CommandPaletteCard({ entries = [], className = '' }) {
  const rows = entries.length > 0
    ? entries.slice(0, 5).map((e, i) => ({
        icon: <Bug size={16} className="text-accent-blue" />,
        label: e.title || e.id,
        shortcut: i === 0 ? '⏎' : null,
      }))
    : mockRows;

  return (
    <div className={`bg-surface border border-hairline rounded-xl overflow-hidden ${className}`}>
      {/* macOS title bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-hairline">
        <div className="flex gap-1.5">
          <span className="w-3 h-3 rounded-full bg-accent-red/60" />
          <span className="w-3 h-3 rounded-full bg-accent-yellow/60" />
          <span className="w-3 h-3 rounded-full bg-accent-green/60" />
        </div>
        <div className="flex-1 ml-2">
          <div className="flex items-center gap-2 bg-surface-elevated rounded-md px-3 py-1.5 border border-hairline">
            <Search size={14} className="text-mute" />
            <span className="text-body-sm text-mute">Search debug knowledge...</span>
            <div className="ml-auto flex items-center gap-1">
              <Keycap>⌘</Keycap>
              <Keycap>K</Keycap>
            </div>
          </div>
        </div>
      </div>

      {/* Command rows */}
      <div className="py-1.5 px-2">
        {rows.map((row, i) => (
          <div
            key={i}
            className={`
              flex items-center gap-3 px-2.5 py-1.5 rounded-sm
              transition-colors duration-100
              ${i === 0 ? 'bg-surface-card' : 'hover:bg-surface-card'}
            `.trim()}
          >
            <div className="w-8 h-8 rounded-md bg-surface-card border border-hairline flex items-center justify-center shrink-0">
              {row.icon}
            </div>
            <span className="text-body-md text-on-dark truncate flex-1">
              {row.label}
            </span>
            {row.shortcut && <Keycap>{row.shortcut}</Keycap>}
          </div>
        ))}
      </div>

      {/* Footer hints */}
      <div className="flex items-center justify-end gap-3 px-4 py-2 border-t border-hairline">
        <div className="flex items-center gap-1">
          <Keycap>↑</Keycap>
          <Keycap>↓</Keycap>
          <span className="text-caption-sm text-mute ml-1">Navigate</span>
        </div>
        <div className="flex items-center gap-1">
          <Keycap>⏎</Keycap>
          <span className="text-caption-sm text-mute ml-1">Open</span>
        </div>
        <div className="flex items-center gap-1">
          <Keycap>Esc</Keycap>
          <span className="text-caption-sm text-mute ml-1">Close</span>
        </div>
      </div>
    </div>
  );
}
