// ====== Particle System ======

export interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  a: number;
  clr: string;
}

export interface MousePosition {
  x: number;
  y: number;
}

// ====== Edit Mode ======

export interface EditModeConfig {
  /** CSS selector for the logo element that triggers login */
  logoSelector?: string;
  /** Number of clicks to trigger login (default: 5) */
  clickThreshold?: number;
  /** CSS selectors for editable elements */
  editableSelectors?: string[];
  /** If true, use modal login instead of prompt() */
  useModalLogin?: boolean;
  /** DOM ID of the modal element */
  modalId?: string;
  /** DOM ID of the password input element */
  passwordInputId?: string;
  /** If true, clean DOM elements before GitHub sync */
  cleanDomBeforeSync?: boolean;
  /** IDs of elements to remove before sync */
  cleanupIds?: string[];
  /** DOM ID of the admin bar element */
  adminBarId?: string;
  /** Key prefix for localStorage (default: 'sw_edits_') */
  storageKeyPrefix?: string;
  /** Key prefix for edit data entries (default: 'e_') */
  dataKeyPrefix?: string;
  /** DOM ID of the edit hint element */
  editHintId?: string;
}

export interface EditModeHandle {
  showLogin: () => void;
}

// ====== Music Player ======

export interface MusicItem {
  name: string;
  url: string;
  type: 'url' | 'file';
}

// ====== GitHub Sync ======

export interface GitHubFileResponse {
  sha: string;
  name: string;
  path: string;
}

export interface GitHubSyncPayload {
  message: string;
  content: string;
  sha: string;
}
