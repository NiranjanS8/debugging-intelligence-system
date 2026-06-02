export default function Keycap({ children, className = '' }) {
  return (
    <kbd
      className={`
        inline-flex items-center justify-center
        keycap-gradient
        text-body text-caption-md
        px-1.5 h-5
        rounded-xs
        border border-hairline
        select-none
        ${className}
      `.trim()}
    >
      {children}
    </kbd>
  );
}
