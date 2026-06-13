/* ========== 粒子系统 ========== */
function initParticles(count) {
  const c = document.getElementById('particles');
  if (!c) return;
  const x = c.getContext('2d');
  let ps = [];
  let m = { x: -1000, y: -1000 };

  function resize() { c.width = innerWidth; c.height = innerHeight; }
  resize();
  onresize = resize;
  onmousemove = e => { m.x = e.clientX; m.y = e.clientY; };

  function P() {
    this.x = Math.random() * c.width;
    this.y = Math.random() * c.height;
    this.vx = (Math.random() - .5) * .6;
    this.vy = (Math.random() - .5) * .6;
    this.r = Math.random() * 2.5 + 1;
    this.a = Math.random() * .5 + .2;
    this.clr = Math.random() > .7 ? '165,94,234' : '0,210,255';
  }

  for (let i = 0; i < count; i++) ps.push(new P());

  (function draw() {
    x.clearRect(0, 0, c.width, c.height);
    ps.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > c.width) p.vx *= -1;
      if (p.y < 0 || p.y > c.height) p.vy *= -1;
      const dx = m.x - p.x, dy = m.y - p.y, dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 200) { p.vx += dx * .00005; p.vy += dy * .00005; }
      x.beginPath();
      x.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      x.fillStyle = `rgba(${p.clr},${p.a})`;
      x.fill();
    });
    for (let i = 0; i < ps.length; i++) {
      for (let j = i + 1; j < ps.length; j++) {
        const dx = ps[i].x - ps[j].x, dy = ps[i].y - ps[j].y, dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150) {
          x.beginPath(); x.moveTo(ps[i].x, ps[i].y); x.lineTo(ps[j].x, ps[j].y);
          x.strokeStyle = `rgba(${ps[i].clr},${.2 * (1 - dist / 150)})`;
          x.lineWidth = .8; x.stroke();
        }
      }
    }
    ps.forEach(p => {
      const dx = m.x - p.x, dy = m.y - p.y, dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 200) {
        x.beginPath(); x.moveTo(p.x, p.y); x.lineTo(m.x, m.y);
        x.strokeStyle = `rgba(0,210,255,${.3 * (1 - dist / 200)})`;
        x.lineWidth = 1; x.stroke();
      }
    });
    requestAnimationFrame(draw);
  })();
}

/* ========== 滚动淡入 ========== */
function initFadeIn() {
  document.querySelectorAll('.fade-in').forEach(el => {
    new IntersectionObserver(es => {
      es.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: .2 }).observe(el);
  });
}

/* ========== 编辑系统 ========== */
const ADMIN_PWD = 'ssbuxi2026';
const GH_TOKEN = atob('Z2hwXzFYVHpQc0V2eGtBbDFxckZ3bkRlNGh5UkVkNEt1djE1WTZlSQ==');
const GH_OWNER = 'yjx123666';
const GH_REPO = 'yjx123666.github.io';

let clickCount = 0;
let clickTimer = null;

function initEditMode() {
  const logo = document.getElementById('logo');
  if (!logo) return;
  logo.addEventListener('click', () => {
    clickCount++;
    clearTimeout(clickTimer);
    clickTimer = setTimeout(() => { clickCount = 0; }, 2000);
    if (clickCount >= 5) { clickCount = 0; showLogin(); }
  });
}

function showLogin() {
  const pwd = prompt('输入管理员密码：');
  if (pwd === ADMIN_PWD) enableEditMode();
  else if (pwd) alert('密码错误');
}

function enableEditMode() {
  document.getElementById('adminBar').style.display = 'block';
  const editables = ['.page-header h1', '.page-header p', '.block h2', '.block p', '.block li', '.card-body h3', '.card-body p'];
  editables.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => { el.contentEditable = 'true'; });
  });
}

function saveEdits() {
  const data = {};
  document.querySelectorAll('[contenteditable="true"]').forEach((el, i) => { data['e_' + i] = el.innerHTML; });
  localStorage.setItem('sw_edits_' + location.pathname, JSON.stringify(data));
  syncToGitHub();
}

function loadEdits() {
  const s = localStorage.getItem('sw_edits_' + location.pathname);
  if (!s) return;
  try {
    const d = JSON.parse(s);
    document.querySelectorAll('[contenteditable="true"]').forEach((el, i) => {
      if (d['e_' + i] !== undefined) el.innerHTML = d['e_' + i];
    });
  } catch (e) {}
}

function exitEdit() {
  document.getElementById('adminBar').style.display = 'none';
  document.querySelectorAll('[contenteditable]').forEach(el => { el.contentEditable = 'false'; });
}

async function syncToGitHub() {
  const bar = document.getElementById('adminBar');
  bar.innerHTML = '正在同步... <button onclick="exitEdit()">退出</button>';
  try {
    document.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
    let html = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
    const u = `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/contents/${location.pathname.split('/').pop()}`;
    const r = await fetch(u, { headers: { 'Authorization': 'token ' + GH_TOKEN } });
    const d = await r.json();
    const resp = await fetch(u, {
      method: 'PUT',
      headers: { 'Authorization': 'token ' + GH_TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: '更新 ' + location.pathname.split('/').pop(),
        content: btoa(unescape(encodeURIComponent(html))),
        sha: d.sha
      })
    });
    if (resp.ok) {
      localStorage.removeItem('sw_edits_' + location.pathname);
      bar.innerHTML = '同步成功！ <button onclick="location.reload()">刷新</button> <button onclick="exitEdit()">退出</button>';
    } else throw new Error('失败');
  } catch (e) {
    bar.innerHTML = '同步失败: ' + e.message + ' <button onclick="syncToGitHub()">重试</button> <button onclick="exitEdit()">退出</button>';
    enableEditMode();
  }
}
