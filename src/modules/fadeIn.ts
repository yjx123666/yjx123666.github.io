export function initFadeIn(): void {
  document.querySelectorAll<HTMLElement>('.fade-in').forEach((el) => {
    const observer = new IntersectionObserver(
      (entries: IntersectionObserverEntry[]) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        }
      },
      { threshold: 0.2 }
    );
    observer.observe(el);
  });
}
