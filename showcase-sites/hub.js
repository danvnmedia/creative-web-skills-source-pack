// Reveal only when motion is welcome; all cards remain visible without JavaScript.
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && 'IntersectionObserver' in window) {
  const cards = document.querySelectorAll('.project');
  document.body.classList.add('can-reveal');
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px 80px 0px', threshold: .06 });
  cards.forEach((card) => observer.observe(card));
}
