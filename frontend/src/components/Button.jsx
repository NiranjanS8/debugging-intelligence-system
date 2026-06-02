import { forwardRef } from 'react';

const variants = {
  primary:
    'bg-primary text-on-primary hover:bg-primary-pressed active:bg-primary-pressed transition-colors duration-150',
  secondary:
    'bg-transparent text-on-dark border border-hairline hover:border-hairline-strong transition-colors duration-150',
  tertiary:
    'bg-surface-elevated text-on-dark hover:bg-surface-card transition-colors duration-150',
  disabled:
    'bg-surface-elevated text-ash cursor-not-allowed',
  ghost:
    'bg-transparent text-body hover:text-on-dark transition-colors duration-150',
};

const sizes = {
  sm: 'h-8 px-3 text-caption-md',
  md: 'h-9 px-4 text-button-md',
  lg: 'h-11 px-6 text-body-md',
};

const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', className = '', children, disabled, ...props },
  ref
) {
  const isDisabled = disabled || variant === 'disabled';
  const variantClasses = isDisabled ? variants.disabled : variants[variant] || variants.primary;
  const sizeClasses = sizes[size] || sizes.md;

  return (
    <button
      ref={ref}
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center gap-2
        rounded-md font-medium
        cursor-pointer select-none
        ${variantClasses}
        ${sizeClasses}
        ${className}
      `.trim()}
      {...props}
    >
      {children}
    </button>
  );
});

export default Button;
