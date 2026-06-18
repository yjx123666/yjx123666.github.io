/**
 * 评论系统 - 基于 Gitalk (GitHub Issues)
 * 免费、无需后端、支持 Markdown
 */

class CommentSystem {
  constructor() {
    this.config = {
      owner: 'yjx123666',           // GitHub 用户名
      repo: 'yjx123666.github.io', // 仓库名
      admin: ['yjx123666'],         // 管理员
      id: window.location.pathname, // 使用页面路径作为 issue ID
      distractionFreeMode: false,   // 无干扰模式
      pagerDirection: 'last',       // 评论排序方向
      perPage: 10,                  // 每页评论数
    };
  }

  // 初始化评论系统
  init() {
    // 检查是否已有评论容器
    const container = document.getElementById('gitalk-container');
    if (!container) return;

    // 加载 Gitalk CSS
    this.loadCSS();

    // 加载 Gitalk JS
    this.loadJS(() => {
      this.render(container);
    });
  }

  // 加载 CSS
  loadCSS() {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/gitalk@1.7.2/dist/gitalk.css';
    document.head.appendChild(link);

    // 添加自定义样式
    const style = document.createElement('style');
    style.textContent = `
      #gitalk-container {
        margin-top: 40px;
        padding-top: 40px;
        border-top: 1px solid var(--ridge);
      }

      .gt-header {
        background: var(--slate) !important;
        border: 1px solid var(--ridge) !important;
        border-radius: 8px !important;
      }

      .gt-header-textarea {
        background: var(--ink) !important;
        color: var(--ash) !important;
        border: 1px solid var(--ridge) !important;
        border-radius: 4px !important;
      }

      .gt-header-textarea:focus {
        border-color: var(--amber) !important;
      }

      .gt-btn {
        background: var(--amber) !important;
        color: var(--ink) !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
      }

      .gt-btn:hover {
        opacity: 0.9 !important;
      }

      .gt-comment {
        background: var(--slate) !important;
        border: 1px solid var(--ridge) !important;
        border-radius: 8px !important;
        margin-bottom: 16px !important;
      }

      .gt-comment-body {
        color: var(--ash) !important;
      }

      .gt-comment-header {
        background: transparent !important;
        border-bottom: 1px solid var(--ridge) !important;
      }

      .gt-comment-username {
        color: var(--amber) !important;
      }

      .gt-comment-date {
        color: var(--fog) !important;
      }

      .gt-comment-content {
        padding: 16px !important;
      }

      .gt-avatar {
        border-radius: 50% !important;
      }

      .gt-link {
        color: var(--amber) !important;
      }

      .gt-link:hover {
        color: var(--cyan) !important;
      }

      .gt-svg {
        fill: var(--amber) !important;
      }

      .gt-count {
        color: var(--amber) !important;
      }

      /* 浅色主题适配 */
      [data-theme="light"] .gt-header {
        background: #ffffff !important;
        border-color: #e9ecef !important;
      }

      [data-theme="light"] .gt-header-textarea {
        background: #f8f9fa !important;
        color: #212529 !important;
        border-color: #e9ecef !important;
      }

      [data-theme="light"] .gt-comment {
        background: #ffffff !important;
        border-color: #e9ecef !important;
      }

      [data-theme="light"] .gt-comment-body {
        color: #212529 !important;
      }
    `;
    document.head.appendChild(style);
  }

  // 加载 JS
  loadJS(callback) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/gitalk@1.7.2/dist/gitalk.min.js';
    script.onload = callback;
    document.head.appendChild(script);
  }

  // 渲染评论
  render(container) {
    const gitalk = new Gitalk({
      clientID: '',                 // 需要创建 GitHub OAuth App
      clientSecret: '',             // 需要创建 GitHub OAuth App
      repo: this.config.repo,
      owner: this.config.owner,
      admin: this.config.admin,
      id: this.config.id,
      distractionFreeMode: this.config.distractionFreeMode,
      pagerDirection: this.config.pagerDirection,
      perPage: this.config.perPage,
      language: 'zh-CN',
    });

    gitalk.render(container);
  }

  // 创建评论区域 HTML
  static createSection() {
    return `
      <section id="comments" class="fade-in">
        <h2>💬 评论留言</h2>
        <p style="text-align: center; color: var(--fog); margin-bottom: 24px;">
          使用 GitHub 账号登录即可评论
        </p>
        <div id="gitalk-container"></div>
      </section>
    `;
  }
}

// ========================================
// 简化版评论系统（无需 GitHub OAuth）
// ========================================

class SimpleCommentSystem {
  constructor() {
    this.storageKey = 'site_comments';
    this.comments = this.loadComments();
  }

  // 加载评论
  loadComments() {
    const data = localStorage.getItem(this.storageKey);
    return data ? JSON.parse(data) : [];
  }

  // 保存评论
  saveComments() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.comments));
  }

  // 添加评论
  addComment(name, content) {
    const comment = {
      id: Date.now(),
      name: name,
      content: content,
      time: new Date().toLocaleString('zh-CN'),
    };
    this.comments.unshift(comment);
    this.saveComments();
    return comment;
  }

  // 删除评论
  deleteComment(id) {
    this.comments = this.comments.filter(c => c.id !== id);
    this.saveComments();
  }

  // 渲染评论
  render(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const html = `
      <section id="comments" class="fade-in">
        <h2>💬 评论留言</h2>

        <!-- 评论表单 -->
        <div class="comment-form">
          <div class="form-group">
            <label for="commentName">昵称</label>
            <input type="text" id="commentName" placeholder="输入你的昵称" maxlength="20">
          </div>
          <div class="form-group">
            <label for="commentContent">留言内容</label>
            <textarea id="commentContent" placeholder="写下你想说的话..." rows="4" maxlength="500"></textarea>
          </div>
          <button id="submitComment" class="btn-submit">发表留言</button>
        </div>

        <!-- 评论列表 -->
        <div class="comment-list" id="commentList">
          ${this.renderComments()}
        </div>
      </section>
    `;

    container.innerHTML = html;
    this.bindEvents();
  }

  // 渲染评论列表
  renderComments() {
    if (this.comments.length === 0) {
      return '<div class="no-comments">暂无留言，快来抢沙发吧！</div>';
    }

    return this.comments.map(comment => `
      <div class="comment-item" data-id="${comment.id}">
        <div class="comment-header">
          <span class="comment-avatar">${comment.name.charAt(0).toUpperCase()}</span>
          <span class="comment-name">${this.escapeHtml(comment.name)}</span>
          <span class="comment-time">${comment.time}</span>
          <button class="comment-delete" onclick="simpleComments.deleteAndRender(${comment.id})">删除</button>
        </div>
        <div class="comment-body">${this.escapeHtml(comment.content)}</div>
      </div>
    `).join('');
  }

  // HTML 转义
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // 绑定事件
  bindEvents() {
    const submitBtn = document.getElementById('submitComment');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => {
        const name = document.getElementById('commentName').value.trim();
        const content = document.getElementById('commentContent').value.trim();

        if (!name) {
          alert('请输入昵称');
          return;
        }
        if (!content) {
          alert('请输入留言内容');
          return;
        }

        this.addComment(name, content);
        document.getElementById('commentName').value = '';
        document.getElementById('commentContent').value = '';
        this.refreshList();
      });
    }
  }

  // 刷新列表
  refreshList() {
    const list = document.getElementById('commentList');
    if (list) {
      list.innerHTML = this.renderComments();
    }
  }

  // 删除并刷新
  deleteAndRender(id) {
    if (confirm('确定删除这条留言吗？')) {
      this.deleteComment(id);
      this.refreshList();
    }
  }

  // 创建评论区域 HTML
  static createSection() {
    return '<div id="comments-container"></div>';
  }
}

// ========================================
// 初始化
// ========================================

let simpleComments;

document.addEventListener('DOMContentLoaded', () => {
  // 使用简化版评论系统（本地存储）
  simpleComments = new SimpleCommentSystem();

  // 如果页面有评论容器，则渲染
  const container = document.getElementById('comments-container');
  if (container) {
    simpleComments.render('comments-container');
  }
});
