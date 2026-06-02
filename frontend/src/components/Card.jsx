const variantStyles = {
  surface: 'bg-surface border-hairline',
  elevated: 'bg-surface-elevated border-hairline',
  card: 'bg-surface-card border-hairline',
  store: 'bg-surface border-hairline',
};

const paddingMap = {
  surface: 'p-6',
  elevated: 'p-6',
  card: 'p-4',
  store: 'p-4',
};

const radiusMap = {
  surface: 'rounded-lg',
  elevated: 'rounded-lg',
  card: 'rounded-md',
  store: 'rounded-md',
};

export default function Card({
  variant = 'surface',
  className = '',
  hover = true,
  children,
  onClick,
  ...props
}) {
  const base = variantStyles[variant] || variantStyles.surface;
  const padding = paddingMap[variant] || 'p-6';
  const radius = radiusMap[variant] || 'rounded-lg';
  const hoverClass = hover
    ? 'hover:border-hairline-strong transition-colors duration-200 cursor-pointer'
    : '';
  const clickHandler = onClick ? { onClick, role: 'button', tabIndex: 0 } : {};

  return (
    <div
      className={`
        border ${base} ${padding} ${radius} ${hoverClass} ${className}
      `.trim()}
      {...clickHandler}
      {...props}
    >
      {children}
    </div>
  );
}
