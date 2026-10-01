const menuButton = document.querySelector('.menu-button');
const menuPanel = document.querySelector('.menu-panel');
const progress = document.querySelector('.progress span');
const hero = document.querySelector('.hero');
const openingCurtain = document.querySelector('.opening-curtain');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

setTimeout(() => document.body.classList.add('is-ready'), reducedMotion ? 0 : 80);
setTimeout(() => {
  openingCurtain.hidden = true;
  document.body.classList.add('opening-complete');
}, reducedMotion ? 0 : 1400);

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
  if (event.key === 'Tab' && !menuPanel.hidden) {
    const links = [...menuPanel.querySelectorAll('a')];
    if (event.shiftKey && document.activeElement === links[0]) {
      event.preventDefault();
      links.at(-1).focus();
    } else if (!event.shiftKey && document.activeElement === links.at(-1)) {
      event.preventDefault();
      links[0].focus();
    }
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

const nativeProgress = CSS.supports('animation-timeline: scroll()');
let scrollQueued = false;
function updateProgress() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const value = scrollable > 0 ? window.scrollY / scrollable : 0;
  if (!nativeProgress) progress.style.transform = `scaleX(${value})`;
  if (!reducedMotion) hero.style.setProperty('--hero-progress', Math.min(window.scrollY / window.innerHeight, 1).toFixed(3));
  scrollQueued = false;
}

function queueProgress() {
  if (scrollQueued) return;
  scrollQueued = true;
  requestAnimationFrame(updateProgress);
}

let pointerQueued = false;
let pointerPosition;
let heroBounds;
function measureHero() {
  const box = hero.getBoundingClientRect();
  heroBounds = { left: box.left + window.scrollX, top: box.top + window.scrollY, width: box.width, height: box.height };
}
measureHero();
window.addEventListener('resize', measureHero, { passive: true });
hero.addEventListener('pointermove', (event) => {
  if (reducedMotion) return;
  pointerPosition = { x: event.clientX, y: event.clientY };
  if (pointerQueued) return;
  pointerQueued = true;
  requestAnimationFrame(() => {
    hero.style.setProperty('--pointer-x', (((pointerPosition.x + window.scrollX - heroBounds.left) / heroBounds.width) * 2 - 1).toFixed(3));
    hero.style.setProperty('--pointer-y', (((pointerPosition.y + window.scrollY - heroBounds.top) / heroBounds.height) * 2 - 1).toFixed(3));
    pointerQueued = false;
  });
}, { passive: true });
hero.addEventListener('pointerleave', () => {
  hero.style.setProperty('--pointer-x', 0);
  hero.style.setProperty('--pointer-y', 0);
});

updateProgress();
window.addEventListener('scroll', queueProgress, { passive: true });
