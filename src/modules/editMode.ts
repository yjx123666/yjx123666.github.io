import type { EditModeConfig, EditModeHandle, GitHubFileResponse } from '../types';
import { ADMIN_PWD, GH_TOKEN, GH_OWNER, GH_REPO } from '../config/constants';

const DEFAULT_CONFIG: Required<EditModeConfig> = {
  logoSelector: '#logo',
  clickThreshold: 5,
  editableSelectors: [
    '.page-header h1',
    '.page-header p',
    '.block h2',
    '.block p',
    '.block li',
    '.card-body h3',
    '.card-body p',
  ],
  useModalLogin: false,
  modalId: 'loginModal',
  passwordInputId: 'pwdInput',
  cleanDomBeforeSync: false,
  cleanupIds: [],
  adminBarId: 'adminBar',
  storageKeyPrefix: 'sw_edits_',
  dataKeyPrefix: 'e_',
  editHintId: 'editHint',
};

function resolveConfig(config?: EditModeConfig): Required<EditModeConfig> {
  return { ...DEFAULT_CONFIG, ...config };
}

function getStorageKey(config: Required<EditModeConfig>): string {
  return config.storageKeyPrefix + location.pathname;
}

export function initEditMode(config?: EditModeConfig): EditModeHandle {
  const cfg = resolveConfig(config);

  // Wire up logo click counter
  let clickCount = 0;
  let clickTimer: ReturnType<typeof setTimeout> | null = null;
  const logo = document.querySelector<HTMLElement>(cfg.logoSelector);

  if (logo) {
    logo.addEventListener('click', () => {
      clickCount++;
      if (clickTimer) clearTimeout(clickTimer);
      clickTimer = setTimeout(() => {
        clickCount = 0;
      }, 2000);
      if (clickCount >= cfg.clickThreshold) {
        clickCount = 0;
        showLogin(cfg);
      }
    });
  }

  // Wire up modal login if enabled
  if (cfg.useModalLogin) {
    const modal = document.getElementById(cfg.modalId);
    const loginBtn = modal?.querySelector('button:first-of-type');
    const cancelBtn = modal?.querySelector('button:last-of-type');

    loginBtn?.addEventListener('click', () => tryLogin(cfg));
    cancelBtn?.addEventListener('click', () => closeLogin(cfg));

    // Enter key in password input
    const pwdInput = document.getElementById(cfg.passwordInputId) as HTMLInputElement | null;
    pwdInput?.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Enter') tryLogin(cfg);
    });
  }

  // Load saved edits
  loadEdits(cfg);

  // Expose global functions for inline onclick handlers
  const win = window as unknown as Record<string, (...args: unknown[]) => void>;
  win['saveEdits'] = () => saveEdits(cfg);
  win['exitEdit'] = () => exitEdit(cfg);
  win['syncToGitHub'] = () => syncToGitHub(cfg);

  return {
    showLogin: () => showLogin(cfg),
  };
}

function showLogin(cfg: Required<EditModeConfig>): void {
  if (cfg.useModalLogin) {
    const modal = document.getElementById(cfg.modalId);
    if (modal) {
      modal.style.display = 'flex';
      const pwdInput = document.getElementById(cfg.passwordInputId) as HTMLInputElement | null;
      pwdInput?.focus();
    }
  } else {
    const pwd = prompt('输入管理员密码：');
    if (pwd === ADMIN_PWD) {
      enableEditMode(cfg);
    } else if (pwd) {
      alert('密码错误');
    }
  }
}

function closeLogin(cfg: Required<EditModeConfig>): void {
  const modal = document.getElementById(cfg.modalId);
  if (modal) {
    modal.style.display = 'none';
  }
}

function tryLogin(cfg: Required<EditModeConfig>): void {
  const pwdInput = document.getElementById(cfg.passwordInputId) as HTMLInputElement | null;
  const pwd = pwdInput?.value ?? '';
  if (pwd === ADMIN_PWD) {
    closeLogin(cfg);
    enableEditMode(cfg);
  } else {
    alert('密码错误');
  }
}

function enableEditMode(cfg: Required<EditModeConfig>): void {
  const adminBar = document.getElementById(cfg.adminBarId);
  if (adminBar) {
    adminBar.style.display = 'block';
  }

  for (const selector of cfg.editableSelectors) {
    document.querySelectorAll<HTMLElement>(selector).forEach((el) => {
      el.contentEditable = 'true';
    });
  }
}

function saveEdits(cfg: Required<EditModeConfig>): void {
  const data: Record<string, string> = {};
  document.querySelectorAll<HTMLElement>('[contenteditable="true"]').forEach((el, i) => {
    data[cfg.dataKeyPrefix + i] = el.innerHTML;
  });
  localStorage.setItem(getStorageKey(cfg), JSON.stringify(data));
  syncToGitHub(cfg);
}

function loadEdits(cfg: Required<EditModeConfig>): void {
  const saved = localStorage.getItem(getStorageKey(cfg));
  if (!saved) return;
  try {
    const data = JSON.parse(saved) as Record<string, string>;
    document.querySelectorAll<HTMLElement>('[contenteditable="true"]').forEach((el, i) => {
      const key = cfg.dataKeyPrefix + i;
      if (data[key] !== undefined) {
        el.innerHTML = data[key];
      }
    });
  } catch {
    // Ignore parse errors
  }
}

function exitEdit(cfg: Required<EditModeConfig>): void {
  const adminBar = document.getElementById(cfg.adminBarId);
  if (adminBar) {
    adminBar.style.display = 'none';
  }
  document.querySelectorAll<HTMLElement>('[contenteditable]').forEach((el) => {
    el.contentEditable = 'false';
  });
}

async function syncToGitHub(cfg: Required<EditModeConfig>): Promise<void> {
  const statusEl = document.getElementById(cfg.adminBarId);
  if (!statusEl) return;

  statusEl.innerHTML = '正在同步到 GitHub... <button onclick="exitEdit()">退出编辑</button>';

  try {
    // Remove contentEditable before capturing HTML
    document.querySelectorAll<HTMLElement>('[contenteditable]').forEach((el) => {
      el.removeAttribute('contenteditable');
    });

    let html = document.documentElement.outerHTML;

    // Clean DOM before sync if configured
    if (cfg.cleanDomBeforeSync && cfg.cleanupIds.length > 0) {
      const tempDoc = new DOMParser().parseFromString(html, 'text/html');
      for (const id of cfg.cleanupIds) {
        const el = tempDoc.getElementById(id);
        if (el) el.remove();
      }
      html = '<!DOCTYPE html>\n' + tempDoc.documentElement.outerHTML;
    } else {
      html = '<!DOCTYPE html>\n' + html;
    }

    // Fetch current file SHA
    const fileName = location.pathname.split('/').pop() || 'index.html';
    const apiUrl = `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/contents/${fileName}`;
    const getResp = await fetch(apiUrl, {
      headers: { Authorization: 'token ' + GH_TOKEN },
    });
    const fileData = (await getResp.json()) as GitHubFileResponse;

    // Push updated content
    const putResp = await fetch(apiUrl, {
      method: 'PUT',
      headers: {
        Authorization: 'token ' + GH_TOKEN,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: '更新 ' + fileName,
        content: btoa(unescape(encodeURIComponent(html))),
        sha: fileData.sha,
      }),
    });

    if (putResp.ok) {
      localStorage.removeItem(getStorageKey(cfg));
      statusEl.innerHTML =
        '同步成功！ <button onclick="location.reload()">刷新</button> <button onclick="exitEdit()">退出</button>';
    } else {
      throw new Error('同步失败');
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : '未知错误';
    statusEl.innerHTML = `同步失败: ${msg} <button onclick="syncToGitHub()">重试</button> <button onclick="exitEdit()">退出</button>`;
    enableEditMode(cfg);
  }
}
