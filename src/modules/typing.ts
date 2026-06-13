interface TextToken {
  type: 'text' | 'tag' | 'entity';
  content: string;
}

export function initTypingAnimation(): void {
  const text = '你好，我是 <span style="color:#00d2ff">伤口</span>';
  const el = document.getElementById('heroTitle');
  if (!el) return;

  const tokens: TextToken[] = [];

  // Pre-parse text, separating HTML tags and normal characters
  function parseText(): void {
    let inTag = false;
    let inEntity = false;
    let current = '';

    for (let j = 0; j < text.length; j++) {
      const char = text[j];

      if (char === '<') {
        if (current) tokens.push({ type: 'text', content: current });
        current = '<';
        inTag = true;
      } else if (char === '>') {
        current += '>';
        tokens.push({ type: 'tag', content: current });
        current = '';
        inTag = false;
      } else if (char === '&' && !inTag) {
        if (current) tokens.push({ type: 'text', content: current });
        current = '&';
        inEntity = true;
      } else if (char === ';' && inEntity) {
        current += ';';
        tokens.push({ type: 'entity', content: current });
        current = '';
        inEntity = false;
      } else if (inTag || inEntity) {
        current += char;
      } else {
        current += char;
      }
    }
    if (current) tokens.push({ type: 'text', content: current });
  }

  parseText();

  // Create a character span element
  function createCharElement(char: string, _index: number): HTMLSpanElement {
    const span = document.createElement('span');
    span.className = 'char';

    if (char === '伤' || char === '口') {
      span.classList.add('highlight-char');
    }

    span.textContent = char;
    return span;
  }

  // Typing animation
  function typeText(): void {
    el!.classList.add('typing-cursor', 'typing-active');

    let charIndex = 0;
    let currentDelay = 0;

    for (const item of tokens) {
      if (item.type === 'tag' || item.type === 'entity') {
        // Insert HTML tags and entities directly
        const content = item.content;
        setTimeout(() => {
          el!.insertAdjacentHTML('beforeend', content);
        }, currentDelay);
      } else {
        // Normal text: reveal character by character
        for (let k = 0; k < item.content.length; k++) {
          const char = item.content[k];
          const delay = currentDelay + k * 70;

          setTimeout(() => {
            const span = createCharElement(char, charIndex);
            span.style.animationDelay = `${charIndex * 0.06}s`;
            el!.appendChild(span);
            charIndex++;
          }, delay);
        }
        currentDelay += item.content.length * 70;
      }
    }

    // Typing complete
    const totalDuration = currentDelay + 500;
    setTimeout(() => {
      el!.classList.remove('typing-cursor', 'typing-active');
      el!.classList.add('typing-complete');
    }, totalDuration);
  }

  // Delay start
  setTimeout(typeText, 600);
}
