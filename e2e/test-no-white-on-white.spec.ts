import { test, expect } from '@playwright/test';

test('no white text on white background anywhere', async ({ page }) => {
  await page.goto('/');

  const violations = await page.evaluate(() => {
    const isVisible = (el: Element) => {
      const r = (el as HTMLElement).getBoundingClientRect();
      return !!(r.width || r.height || (el as HTMLElement).getClientRects().length);
    };

    const isWhite = (s: string | null) => {
      if (!s) return false;
      const t = s.replace(/\s+/g, '').toLowerCase();
      return t === 'rgb(255,255,255)' || t === 'rgba(255,255,255,1)' || t === '#ffffff' || t === 'white';
    };

    const nodes = Array.from(document.querySelectorAll<HTMLElement>('*'));
    const out: Array<{ path: string; text: string | null }> = [];

    for (const el of nodes) {
      if (!isVisible(el)) continue;
      const cs = window.getComputedStyle(el);
      if (!isWhite(cs.color)) continue; // only interested in white foreground

      // walk up ancestors to see if any background is explicitly white
      let node: HTMLElement | null = el;
      while (node) {
        const bg = window.getComputedStyle(node).backgroundColor;
        if (isWhite(bg)) {
          const path = node.tagName.toLowerCase() + (node.id ? `#${node.id}` : '') + (node.className ? `.${node.className.split(' ').join('.')}` : '');
          out.push({ path, text: el.textContent ? el.textContent.trim().slice(0, 80) : null });
          break;
        }
        node = node.parentElement;
      }
    }

    return out;
  });

  expect(violations.length, `White-on-white violations found: ${JSON.stringify(violations, null, 2)}`).toBe(0);
});
