import { Inbox } from 'lucide-react';

export default function EmptyState({
  icon: Icon = Inbox,
  title = 'No data yet',
  description = 'There\'s nothing to show right now.',
  children,
  className = '',
}) {
  return (
    <div className={`flex flex-col items-center justify-center py-16 px-4 ${className}`}>
      <div className="w-14 h-14 rounded-xl bg-surface-elevated border border-hairline flex items-center justify-center mb-5">
        <Icon size={24} className="text-mute" />
      </div>
      <h3 className="text-heading-sm text-ink mb-2">{title}</h3>
      <p className="text-body-sm text-mute text-center max-w-sm mb-6">{description}</p>
      {children}
    </div>
  );
}
