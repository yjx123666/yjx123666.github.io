import type { MusicItem } from '../types';

let musicPlaying = false;
let musicPanelOpen = false;
let musicList: MusicItem[] = [];
let currentMusicIndex = 0;

function getAudioElement(): HTMLAudioElement | null {
  return document.getElementById('bgMusic') as HTMLAudioElement | null;
}

function toggleMusic(): void {
  const audio = getAudioElement();
  const btn = document.getElementById('musicBtn');
  if (!audio || !btn) return;

  if (musicPlaying) {
    audio.pause();
    btn.classList.remove('playing');
    btn.textContent = '♪';
  } else {
    audio.play().catch(() => {});
    btn.classList.add('playing');
    btn.textContent = '♫';
  }
  musicPlaying = !musicPlaying;
}

function toggleMusicPanel(): void {
  musicPanelOpen = !musicPanelOpen;
  const panel = document.getElementById('musicPanel');
  if (!panel) return;

  if (musicPanelOpen) {
    panel.classList.add('show');
  } else {
    panel.classList.remove('show');
  }
}

function extractMusicName(url: string): string {
  try {
    const urlObj = new URL(url);
    const pathname = urlObj.pathname;
    const filename = pathname.split('/').pop() || '';
    return filename.replace(/\.[^/.]+$/, '') || '未知音乐';
  } catch {
    return '未知音乐';
  }
}

function saveMusicList(): void {
  localStorage.setItem('musicList', JSON.stringify(musicList));
  localStorage.setItem('currentMusicIndex', currentMusicIndex.toString());
}

function renderMusicList(): void {
  const container = document.getElementById('musicList');
  if (!container) return;

  container.innerHTML = '';

  musicList.forEach((music, index) => {
    const item = document.createElement('div');
    item.className = `music-item ${index === currentMusicIndex ? 'active' : ''}`;

    const name = document.createElement('span');
    name.className = 'music-item-name';
    name.textContent = music.name;
    name.title = music.name;

    const playBtn = document.createElement('button');
    playBtn.className = 'music-item-btn';
    playBtn.textContent = index === currentMusicIndex ? '⏸' : '▶';
    playBtn.addEventListener('click', () => playMusic(index));

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'music-item-btn delete';
    deleteBtn.textContent = '×';
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteMusic(index);
    });

    item.appendChild(name);
    item.appendChild(playBtn);
    item.appendChild(deleteBtn);
    container.appendChild(item);
  });
}

function playMusic(index: number): void {
  if (index === currentMusicIndex && musicPlaying) {
    toggleMusic();
    return;
  }

  currentMusicIndex = index;
  const music = musicList[index];
  const audio = getAudioElement();
  if (!audio) return;

  audio.src = music.url;
  audio.load();

  audio
    .play()
    .then(() => {
      musicPlaying = true;
      const btn = document.getElementById('musicBtn');
      if (btn) {
        btn.classList.add('playing');
        btn.textContent = '♫';
      }
      saveMusicList();
      renderMusicList();
    })
    .catch((err) => {
      console.error('播放失败:', err);
      alert('播放失败，请检查音乐链接是否有效');
    });
}

function deleteMusic(index: number): void {
  if (musicList.length <= 1) {
    alert('至少保留一首音乐');
    return;
  }

  musicList.splice(index, 1);

  if (index === currentMusicIndex) {
    currentMusicIndex = 0;
    playMusic(0);
  } else if (index < currentMusicIndex) {
    currentMusicIndex--;
  }

  saveMusicList();
  renderMusicList();
}

function addMusic(): void {
  const urlInput = document.getElementById('musicUrlInput') as HTMLInputElement | null;
  const fileInput = document.getElementById('musicFileInput') as HTMLInputElement | null;

  const url = urlInput?.value.trim() || '';
  const file = fileInput?.files?.[0];

  if (url) {
    const name = extractMusicName(url);
    musicList.push({ name, url, type: 'url' });
    if (urlInput) urlInput.value = '';
  } else if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      const name = file.name.replace(/\.[^/.]+$/, '');
      musicList.push({ name, url: e.target?.result as string, type: 'file' });
      saveMusicList();
      renderMusicList();
      if (fileInput) fileInput.value = '';
    };
    reader.readAsDataURL(file);
    return;
  } else {
    alert('请输入音乐链接或选择文件');
    return;
  }

  saveMusicList();
  renderMusicList();
}

function initMusicList(): void {
  musicList = JSON.parse(localStorage.getItem('musicList') || '[]') as MusicItem[];
  currentMusicIndex = parseInt(localStorage.getItem('currentMusicIndex') || '0', 10);

  if (musicList.length === 0) {
    musicList.push({
      name: '默认音乐',
      url: 'https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d2.mp3',
      type: 'url',
    });
    saveMusicList();
  }
  renderMusicList();
}

export function initMusic(): void {
  initMusicList();

  // Wire up static button event listeners
  document.getElementById('musicBtn')?.addEventListener('click', toggleMusic);
  document.getElementById('musicSettingsBtn')?.addEventListener('click', toggleMusicPanel);

  // Expose for inline onclick handlers in HTML
  const win = window as unknown as Record<string, (...args: unknown[]) => void>;
  win['toggleMusic'] = toggleMusic;
  win['toggleMusicPanel'] = toggleMusicPanel;
  win['addMusic'] = addMusic;

  // Auto-play on first user interaction
  const handleFirstClick = (): void => {
    const audio = getAudioElement();
    if (!audio) return;

    audio.volume = 0.3;
    audio
      .play()
      .then(() => {
        musicPlaying = true;
        const btn = document.getElementById('musicBtn');
        if (btn) {
          btn.classList.add('playing');
          btn.textContent = '♫';
        }
      })
      .catch(() => {});
    document.removeEventListener('click', handleFirstClick);
  };
  document.addEventListener('click', handleFirstClick, { once: true });
}
