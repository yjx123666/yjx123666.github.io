import '../../style.css';
import { initParticles } from '../modules/particles';
import { initFadeIn } from '../modules/fadeIn';
import { initEditMode } from '../modules/editMode';
import { initTypingAnimation } from '../modules/typing';
import { initContour } from '../modules/contour';

// Background systems
initParticles(50);
initContour();

// Scroll fade-in
initFadeIn();

// Typing animation
initTypingAnimation();

// Edit mode with index page config
const editHandle = initEditMode({
  editableSelectors: [
    '.hero h1',
    '.hero-description',
    '.hero .tag',
    '.card-body h3',
    '.card-body p',
    '.card-tags span',
    '.card-date',
    'footer p',
  ],
  useModalLogin: true,
  modalId: 'loginModal',
  passwordInputId: 'pwdInput',
  cleanDomBeforeSync: true,
  cleanupIds: ['adminBar', 'loginModal', 'editHint'],
  dataKeyPrefix: 'edit_',
});

// Edit hint (only on index page)
if (location.hash === '#edit') {
  const hint = document.getElementById('editHint');
  if (hint) {
    hint.style.display = 'block';
    hint.addEventListener('click', editHandle.showLogin);
  }
}
