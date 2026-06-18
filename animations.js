/**
 * 页面动画和图片懒加载
 */

// ========================================
// 页面切换动画
// ========================================

class PageTransition {
  constructor() {
    this.init();
  }

  init() {
    // 添加页面加载动画
    document.body.classList.add('page-loaded');

    // 监听链接点击
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (link && link.href && !link.href.startsWith('javascript:') && !link.target) {
        this.handleClick(e, link);
      }
    });

    // 监听浏览器前进后退
    window.addEventListener('popstate', () => {
      this.showPage();
    });
  }

  handleClick(e, link) {
    const href = link.href;

    // 检查是否是站内链接
    if (href.includes(window.location.hostname) || href.startsWith('/')) {
      e.preventDefault();
      this.navigateTo(href);
    }
  }

  navigateTo(url) {
    // 添加退出动画
    document.body.classList.add('page-exit');

    setTimeout(() => {
      window.location.href = url;
    }, 300);
  }

  showPage() {
    document.body.classList.remove('page-exit');
    document.body.classList.add('page-enter');

    setTimeout(() => {
      document.body.classList.remove('page-enter');
    }, 300);
  }
}

// ========================================
// 图片懒加载
// ========================================

class LazyLoader {
  constructor() {
    this.observer = null;
    this.init();
  }

  init() {
    // 检查浏览器支持
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.loadImage(entry.target);
            this.observer.unobserve(entry.target);
          }
        });
      }, {
        rootMargin: '50px 0px',
        threshold: 0.01
      });

      this.observeImages();
    } else {
      // 降级处理：直接加载所有图片
      this.loadAllImages();
    }
  }

  observeImages() {
    const images = document.querySelectorAll('img[data-src]');
    images.forEach(img => {
      this.observer.observe(img);
    });
  }

  loadImage(img) {
    const src = img.getAttribute('data-src');
    if (!src) return;

    // 创建新图片预加载
    const newImg = new Image();
    newImg.onload = () => {
      img.src = src;
      img.removeAttribute('data-src');
      img.classList.add('loaded');
    };
    newImg.onerror = () => {
      img.classList.add('error');
    };
    newImg.src = src;
  }

  loadAllImages() {
    const images = document.querySelectorAll('img[data-src]');
    images.forEach(img => this.loadImage(img));
  }

  // 动态添加的图片也需要懒加载
  observe(img) {
    if (this.observer) {
      this.observer.observe(img);
    } else {
      this.loadImage(img);
    }
  }
}

// ========================================
// 滚动动画增强
// ========================================

class ScrollAnimations {
  constructor() {
    this.observer = null;
    this.init();
  }

  init() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.animateElement(entry.target);
            this.observer.unobserve(entry.target);
          }
        });
      }, {
        rootMargin: '0px 0px -50px 0px',
        threshold: 0.1
      });

      this.observeElements();
    }
  }

  observeElements() {
    // 观察所有需要动画的元素
    const elements = document.querySelectorAll('.fade-in, .slide-in, .scale-in');
    elements.forEach(el => {
      this.observer.observe(el);
    });
  }

  animateElement(el) {
    // 根据动画类型添加类名
    if (el.classList.contains('fade-in')) {
      el.classList.add('visible');
    }
    if (el.classList.contains('slide-in')) {
      el.classList.add('visible');
    }
    if (el.classList.contains('scale-in')) {
      el.classList.add('visible');
    }
  }
}

// ========================================
// 平滑滚动
// ========================================

class SmoothScroll {
  constructor() {
    this.init();
  }

  init() {
    // 监听锚点点击
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="#"]');
      if (link) {
        e.preventDefault();
        const targetId = link.getAttribute('href').slice(1);
        const target = document.getElementById(targetId);
        if (target) {
          this.scrollTo(target);
        }
      }
    });
  }

  scrollTo(element, offset = 80) {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }
}

// ========================================
// 初始化所有动画
// ========================================

document.addEventListener('DOMContentLoaded', () => {
  // 页面切换动画
  new PageTransition();

  // 图片懒加载
  window.lazyLoader = new LazyLoader();

  // 滚动动画
  new ScrollAnimations();

  // 平滑滚动
  new SmoothScroll();
});
