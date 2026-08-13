const canvas = document.querySelector('#field-preview');
const context = canvas?.getContext('2d');

function drawField() {
  if (!canvas || !context) return;
  const box = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  canvas.width = Math.round(box.width * dpr);
  canvas.height = Math.round(box.height * dpr);
  context.scale(dpr, dpr);
  context.fillStyle = '#081d24';
  context.fillRect(0, 0, box.width, box.height);
  context.strokeStyle = 'rgba(90, 241, 205, .34)';
  context.lineWidth = 1;
  for (let row = 0; row < 17; row += 1) {
    context.beginPath();
    for (let x = -20; x < box.width + 20; x += 8) {
      const y = box.height * .18 + row * 22 + Math.sin(x * .018 + row * .58) * (10 + row * .7);
      if (x === -20) context.moveTo(x, y); else context.lineTo(x, y);
    }
    context.stroke();
  }
}

drawField();
window.addEventListener('resize', drawField, { passive: true });

const asmePreview = document.querySelector('#asme-preview');
if (asmePreview) {
  new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting && !document.hidden) void asmePreview.play().catch(() => undefined);
    else asmePreview.pause();
  }, { rootMargin: '120px' }).observe(asmePreview);
}