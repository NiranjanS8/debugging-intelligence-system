export default function PillTab({ tabs, activeTab, onTabChange, className = '' }) {
  return (
    <div className={`flex flex-wrap items-center gap-1 ${className}`}>
      {tabs.map((tab) => {
        const isActive = tab === activeTab;
        return (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            className={`
              text-body-sm px-2.5 py-1 rounded-full
              transition-colors duration-150 cursor-pointer
              whitespace-nowrap select-none
              ${
                isActive
                  ? 'bg-surface-elevated text-on-dark'
                  : 'bg-transparent text-body hover:text-on-dark'
              }
            `.trim()}
          >
            {tab}
          </button>
        );
      })}
    </div>
  );
}
