/**
 * 主题切换功能
 * 支持深色/浅色模式切换
 */

class ThemeManager {
  constructor() {
    this.theme = this.getStoredTheme() || this.getSystemTheme();
    this.init();
  }

  // 获取系统主题
  getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  // 获取存储的主题
  getStoredTheme() {
    return localStorage.getItem('theme');
  }

  // 保存主题
  setStoredTheme(theme) {
    localStorage.setItem('theme', theme);
  }

  // 初始化
  init() {
    this.applyTheme(this.theme);
    this.createToggleButton();
    this.listenSystemTheme();
  }

  // 应用主题
  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    this.theme = theme;
    this.setStoredTheme(theme);

    // 更新按钮图标
    const btn = document.querySelector('.theme-toggle');
    if (btn) {
      btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
      btn.setAttribute('title', theme === 'dark' ? '切换到浅色模式' : '切换到深色模式');
    }
  }

  // 切换主题
  toggle() {
    const newTheme = this.theme === 'dark' ? 'light' : 'dark';
    this.applyTheme(newTheme);

    // 添加切换动画
    document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    setTimeout(() => {
      document.body.style.transition = '';
    }, 300);
  }

  // 创建切换按钮
  createToggleButton() {
    const btn = document.createElement('button');
    btn.className = 'theme-toggle';
    btn.innerHTML = this.theme === 'dark' ? '☀️' : '🌙';
    btn.setAttribute('title', this.theme === 'dark' ? '切换到浅色模式' : '切换到深色模式');
    btn.addEventListener('click', () => this.toggle());

    // 添加到导航栏
    const navContact = document.querySelector('.nav-contact');
    if (navContact) {
      navContact.insertBefore(btn, navContact.firstChild);
    }
  }

  // 监听系统主题变化
  listenSystemTheme() {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!this.getStoredTheme()) {
        this.applyTheme(e.matches ? 'dark' : 'light');
      }
    });
  }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  new ThemeManager();
});
