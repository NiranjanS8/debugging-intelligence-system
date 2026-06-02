import { Search } from 'lucide-react';

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search the knowledge base...',
  className = '',
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && onSubmit) {
      onSubmit(value);
    }
  };

  return (
    <div className={`relative ${className}`}>
      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-mute pointer-events-none">
        <Search size={18} />
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="
          w-full h-11 pl-11 pr-4
          bg-surface-elevated text-on-dark
          border border-hairline rounded-md
          text-body-md
          placeholder:text-mute
          outline-none
          focus:border-hairline-strong
          transition-colors duration-150
        "
      />
    </div>
  );
}
