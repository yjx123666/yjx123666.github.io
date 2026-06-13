import type { Particle, MousePosition } from '../types';

export function initParticles(count: number): void {
  const canvas = document.getElementById('particles') as HTMLCanvasElement | null;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const particles: Particle[] = [];
  const mouse: MousePosition = { x: -1000, y: -1000 };

  function resize(): void {
    canvas!.width = window.innerWidth;
    canvas!.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', (e: MouseEvent) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  function createParticle(): Particle {
    return {
      x: Math.random() * canvas!.width,
      y: Math.random() * canvas!.height,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      r: Math.random() * 2.5 + 1,
      a: Math.random() * 0.5 + 0.2,
      clr: Math.random() > 0.7 ? '165,94,234' : '0,210,255',
    };
  }

  for (let i = 0; i < count; i++) {
    particles.push(createParticle());
  }

  function draw(): void {
    ctx!.clearRect(0, 0, canvas!.width, canvas!.height);

    // Update and draw particles
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > canvas!.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas!.height) p.vy *= -1;

      const dx = mouse.x - p.x;
      const dy = mouse.y - p.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 200) {
        p.vx += dx * 0.00005;
        p.vy += dy * 0.00005;
      }

      ctx!.beginPath();
      ctx!.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx!.fillStyle = `rgba(${p.clr},${p.a})`;
      ctx!.fill();
    }

    // Draw connections between nearby particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150) {
          ctx!.beginPath();
          ctx!.moveTo(particles[i].x, particles[i].y);
          ctx!.lineTo(particles[j].x, particles[j].y);
          ctx!.strokeStyle = `rgba(${particles[i].clr},${0.2 * (1 - dist / 150)})`;
          ctx!.lineWidth = 0.8;
          ctx!.stroke();
        }
      }
    }

    // Draw connections to mouse
    for (const p of particles) {
      const dx = mouse.x - p.x;
      const dy = mouse.y - p.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 200) {
        ctx!.beginPath();
        ctx!.moveTo(p.x, p.y);
        ctx!.lineTo(mouse.x, mouse.y);
        ctx!.strokeStyle = `rgba(0,210,255,${0.3 * (1 - dist / 200)})`;
        ctx!.lineWidth = 1;
        ctx!.stroke();
      }
    }

    requestAnimationFrame(draw);
  }

  draw();
}
