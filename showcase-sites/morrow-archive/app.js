const menuButton = document.querySelector('.menu-button');
const menuPanel = document.querySelector('.menu-panel');
const progress = document.querySelector('.progress span');
const hero = document.querySelector('.hero');
const openingCurtain = document.querySelector('.opening-curtain');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

setTimeout(() => document.body.classList.add('is-ready'), 80);
setTimeout(() => {
  openingCurtain.hidden = true;
  document.body.classList.add('opening-complete');
}, 1400);

function setMenu(open) {
  menuButton.setAttribute('aria-expanded', String(open));
  menuPanel.hidden = !open;
  document.body.style.overflow = open ? 'hidden' : '';
  if (open) menuPanel.querySelector('a')?.focus();
}

menuButton.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
menuPanel.addEventListener('click', (event) => {
  if (event.target.closest('a')) setMenu(false);
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !menuPanel.hidden) {
    setMenu(false);
    menuButton.focus();
  }
});

const observed = document.querySelectorAll('.reveal, .image-reveal');
if (reducedMotion) {
  observed.forEach((element) => element.classList.add('is-visible'));
} else {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: .14 });
  observed.forEach((element) => observer.observe(element));
}

function updateProgress() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const value = scrollable > 0 ? window.scrollY / scrollable : 0;
  progress.style.transform = `scaleX(${value})`;
  if (!reducedMotion) hero.style.setProperty('--hero-progress', Math.min(window.scrollY / window.innerHeight, 1).toFixed(3));
}

hero.addEventListener('pointermove', (event) => {
  if (reducedMotion) return;
  const box = hero.getBoundingClientRect();
  hero.style.setProperty('--pointer-x', (((event.clientX - box.left) / box.width) * 2 - 1).toFixed(3));
  hero.style.setProperty('--pointer-y', (((event.clientY - box.top) / box.height) * 2 - 1).toFixed(3));
}, { passive: true });
hero.addEventListener('pointerleave', () => {
  hero.style.setProperty('--pointer-x', 0);
  hero.style.setProperty('--pointer-y', 0);
});

updateProgress();
window.addEventListener('scroll', updateProgress, { passive: true });