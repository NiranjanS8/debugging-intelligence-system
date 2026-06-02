import { forwardRef } from 'react';

const TextInput = forwardRef(function TextInput(
  { label, className = '', error, ...props },
  ref
) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label className="text-body-sm-strong text-on-dark">{label}</label>
      )}
      <input
        ref={ref}
        className={`
          h-9 px-3
          bg-surface-elevated text-on-dark
          border rounded-md
          text-body-md
          placeholder:text-mute
          outline-none
          transition-colors duration-150
          ${error ? 'border-accent-red' : 'border-hairline focus:border-hairline-strong'}
        `.trim()}
        {...props}
      />
      {error && (
        <span className="text-caption-sm text-accent-red">{error}</span>
      )}
    </div>
  );
});

export default TextInput;
