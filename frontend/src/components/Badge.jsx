const variants = {
  pro: 'bg-surface-elevated text-on-dark-mute',
  info: 'bg-accent-blue-soft text-accent-blue',
  success: 'bg-accent-green-soft text-accent-green',
  warning: 'bg-accent-yellow-soft text-accent-yellow',
  error: 'bg-accent-red-soft text-accent-red',
  neutral: 'bg-surface-elevated text-mute',
};

export default function Badge({ variant = 'neutral', className = '', children }) {
  const variantClass = variants[variant] || variants.neutral;
  return (
    <span
      className={`
        inline-flex items-center
        text-caption-sm
        px-2 py-0.5
        rounded-xs
        whitespace-nowrap
        ${variantClass} ${className}
      `.trim()}
    >
      {children}
    </span>
  );
}
