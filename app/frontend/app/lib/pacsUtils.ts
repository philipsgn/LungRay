export function cardiothoracicRatio(cardiacWidth: number, thoracicWidth: number): number {
  return Math.abs(cardiacWidth) / Math.max(0.1, Math.abs(thoracicWidth));
}

export function installPopoverDismissal(element: HTMLElement, close: () => void): () => void {
  const outside = (event: MouseEvent) => { if (!element.contains(event.target as Node)) close(); };
  const keyboard = (event: KeyboardEvent) => {
    if (event.key === "Escape") { close(); element.querySelector("button")?.focus(); }
  };
  document.addEventListener("mousedown", outside);
  document.addEventListener("keydown", keyboard);
  return () => {
    document.removeEventListener("mousedown", outside);
    document.removeEventListener("keydown", keyboard);
  };
}
