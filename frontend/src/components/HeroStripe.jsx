import Button from './Button';

export default function HeroStripe({ title, subtitle, ctaText, onCtaClick, children }) {
  return (
    <section className="hero-stripe-bg relative py-24 md:py-32 lg:py-(--spacing-section)">
      <div className="relative z-10 max-w-[1240px] mx-auto px-6 md:px-12">
        <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16">
          {/* Left: copy */}
          <div className="flex-1 text-center lg:text-left">
            <h1 className="text-display-xl mb-4">
              {title}
            </h1>
            {subtitle && (
              <p className="text-body-lg text-body max-w-xl mx-auto lg:mx-0 mb-8">
                {subtitle}
              </p>
            )}
            {ctaText && (
              <Button size="lg" onClick={onCtaClick}>
                {ctaText}
              </Button>
            )}
          </div>

          {/* Right: hero visual */}
          {children && (
            <div className="flex-1 w-full max-w-xl lg:max-w-none">
              {children}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
