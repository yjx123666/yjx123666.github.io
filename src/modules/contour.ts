/**
 * Topographic contour canvas — the signature visual element.
 * Renders slowly drifting contour lines with elevation labels,
 * evoking a cartographic relief map.
 */

/** Simple 2D Perlin-like noise */
function noise2D(x: number, y: number): number {
  const n = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
  return n - Math.floor(n);
}

function smoothNoise(x: number, y: number): number {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;

  const a = noise2D(ix, iy);
  const b = noise2D(ix + 1, iy);
  const c = noise2D(ix, iy + 1);
  const d = noise2D(ix + 1, iy + 1);

  const ux = fx * fx * (3 - 2 * fx);
  const uy = fy * fy * (3 - 2 * fy);

  return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy;
}

function fbm(x: number, y: number): number {
  let v = 0;
  let amp = 0.5;
  for (let i = 0; i < 4; i++) {
    v += amp * smoothNoise(x, y);
    x *= 2;
    y *= 2;
    amp *= 0.5;
  }
  return v;
}

interface ContourConfig {
  lineColor: string;
  labelColor: string;
  labelSize: number;
}

const DEFAULT_CONFIG: ContourConfig = {
  lineColor: 'rgba(212,160,83,',  // amber
  labelColor: 'rgba(212,160,83,0.22)',
  labelSize: 9,
};

export function initContour(userConfig?: Partial<ContourConfig>): void {
  const canvas = document.getElementById('contourCanvas') as HTMLCanvasElement | null;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const cfg = { ...DEFAULT_CONFIG, ...userConfig };

  const cellSize = 48;
  const numContours = 12;
  const levels = Array.from({ length: numContours }, (_, i) => (i + 1) / (numContours + 1));

  let time = 0;

  function resize(): void {
    canvas!.width = window.innerWidth;
    canvas!.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function draw(): void {
    const w = canvas!.width;
    const h = canvas!.height;
    ctx!.clearRect(0, 0, w, h);

    const cols = Math.ceil(w / cellSize) + 1;
    const rows = Math.ceil(h / cellSize) + 1;

    // Marching squares contour extraction
    for (let levelIdx = 0; levelIdx < levels.length; levelIdx++) {
      const level = levels[levelIdx];
      const alpha = 0.03 + level * 0.14;

      ctx!.strokeStyle = `${cfg.lineColor}${alpha})`;
      ctx!.lineWidth = levelIdx % 3 === 0 ? 1.2 : 0.6;
      ctx!.beginPath();

      for (let row = 0; row < rows - 1; row++) {
        for (let col = 0; col < cols - 1; col++) {
          const x0 = col * cellSize;
          const y0 = row * cellSize;

          // Sample noise at corners with time offset for drift
          const tl = fbm((col + time * 0.012) * 0.3, (row + time * 0.008) * 0.3);
          const tr = fbm((col + 1 + time * 0.012) * 0.3, (row + time * 0.008) * 0.3);
          const bl = fbm((col + time * 0.012) * 0.3, (row + 1 + time * 0.008) * 0.3);
          const br = fbm((col + 1 + time * 0.012) * 0.3, (row + 1 + time * 0.008) * 0.3);

          // Marching squares case index
          let caseIdx = 0;
          if (tl > level) caseIdx |= 8;
          if (tr > level) caseIdx |= 4;
          if (br > level) caseIdx |= 2;
          if (bl > level) caseIdx |= 1;

          if (caseIdx === 0 || caseIdx === 15) continue;

          // Linear interpolation along edges
          const lerp = (a: number, b: number): number => (level - a) / (b - a);

          const topX = x0 + lerp(tl, tr) * cellSize;
          const rightY = y0 + lerp(tr, br) * cellSize;
          const bottomX = x0 + lerp(bl, br) * cellSize;
          const leftY = y0 + lerp(tl, bl) * cellSize;

          const segments: Array<[number, number, number, number]> = [];
          switch (caseIdx) {
            case 1: case 14: segments.push([x0, leftY, bottomX, y0 + cellSize]); break;
            case 2: case 13: segments.push([bottomX, y0 + cellSize, x0 + cellSize, rightY]); break;
            case 3: case 12: segments.push([x0, leftY, x0 + cellSize, rightY]); break;
            case 4: case 11: segments.push([topX, y0, x0 + cellSize, rightY]); break;
            case 5:
              segments.push([x0, leftY, topX, y0]);
              segments.push([bottomX, y0 + cellSize, x0 + cellSize, rightY]);
              break;
            case 6: case 9: segments.push([topX, y0, bottomX, y0 + cellSize]); break;
            case 7: case 8: segments.push([x0, leftY, topX, y0]); break;
            case 10:
              segments.push([topX, y0, x0 + cellSize, rightY]);
              segments.push([x0, leftY, bottomX, y0 + cellSize]);
              break;
          }

          for (const [ax, ay, bx, by] of segments) {
            ctx!.moveTo(ax, ay);
            ctx!.lineTo(bx, by);
          }
        }
      }

      ctx!.stroke();

      // Elevation labels on major contours
      if (levelIdx % 3 === 0 && levelIdx > 0) {
        ctx!.font = `${cfg.labelSize}px "Noto Serif SC", Georgia, serif`;
        ctx!.fillStyle = cfg.labelColor;
        const elevation = Math.round(level * 5000);
        const labelX = (levelIdx * 137 + 50) % (w - 60) + 30;
        const labelY = (levelIdx * 89 + 80) % (h - 40) + 20;
        ctx!.fillText(`${elevation}m`, labelX, labelY);
      }
    }

    time++;
    requestAnimationFrame(draw);
  }

  draw();
}
