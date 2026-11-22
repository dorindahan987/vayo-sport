// ============================
// VAYO — Hero Canvas Background
// ============================

function initHeroBg() {
  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, particles = [], mouse = { x: -999, y: -999 };
  const NUM = 70;
  const MAX_DIST = 140;
  const TEAL = [106, 235, 214];

  function resize() {
    W = canvas.width  = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }

  class Particle {
    constructor() { this.init(); }
    init() {
      this.x  = Math.random() * W;
      this.y  = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.35;
      this.vy = (Math.random() - 0.5) * 0.35;
      this.r  = Math.random() * 1.2 + 0.4;
      this.base_opacity = Math.random() * 0.35 + 0.08;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > W) this.vx *= -1;
      if (this.y < 0 || this.y > H) this.vy *= -1;

      // Mouse repulsion
      const dx = this.x - mouse.x;
      const dy = this.y - mouse.y;
      const md = Math.sqrt(dx * dx + dy * dy);
      if (md < 80) {
        const force = (80 - md) / 80;
        this.x += dx / md * force * 1.5;
        this.y += dy / md * force * 1.5;
      }
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${TEAL[0]},${TEAL[1]},${TEAL[2]},${this.base_opacity})`;
      ctx.fill();
    }
  }

  function connect() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MAX_DIST) {
          const alpha = 0.055 * (1 - dist / MAX_DIST);
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(${TEAL[0]},${TEAL[1]},${TEAL[2]},${alpha})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }

      // Connect to mouse
      const dx = particles[i].x - mouse.x;
      const dy = particles[i].y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 160) {
        const alpha = 0.18 * (1 - dist / 160);
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(mouse.x, mouse.y);
        ctx.strokeStyle = `rgba(${TEAL[0]},${TEAL[1]},${TEAL[2]},${alpha})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }
    }
  }

  function frame() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });
    connect();
    requestAnimationFrame(frame);
  }

  function init() {
    resize();
    particles = Array.from({ length: NUM }, () => new Particle());
    frame();
  }

  canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
  });
  canvas.addEventListener('mouseleave', () => { mouse.x = -999; mouse.y = -999; });
  window.addEventListener('resize', () => { resize(); particles.forEach(p => p.init()); });

  init();
}

// ============================
// CASCADE TEXT — vanilla JS
// ============================
function initCascadeText() {
  document.querySelectorAll('.cascade').forEach(el => {
    const text = el.textContent.trim();
    const chars = [...text];
    el.innerHTML = '';
    el.style.display = 'inline-flex';
    el.style.overflow = 'hidden';
    el.style.height = '1em';

    chars.forEach((ch, i) => {
      const span = document.createElement('span');
      span.style.cssText = `
        display: inline-block;
        position: relative;
        will-change: transform;
        transition: transform 280ms ease-in-out;
        transition-delay: ${i * 22}ms;
        text-shadow: 0 1em currentColor;
      `;
      span.textContent = ch === ' ' ? '\u00A0' : ch;
      el.appendChild(span);
    });

    const parent = el.closest('.cascade-wrap') || el.parentElement;
    parent.addEventListener('mouseenter', () => {
      el.querySelectorAll('span').forEach(s => {
        s.style.transform = 'translateY(-1em)';
      });
    });
    parent.addEventListener('mouseleave', () => {
      el.querySelectorAll('span').forEach(s => {
        s.style.transform = 'translateY(0)';
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initHeroBg();
  // cascade runs after setLang() has written the translated text
  setTimeout(initCascadeText, 50);
});
