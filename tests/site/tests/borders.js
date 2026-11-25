// Run in the page: every place where two borders meet (a double line), and every framed box inside another framed box.
(() => {
  const out = [];
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const has = (e, k) => { const s = getComputedStyle(e); return parseFloat(s['border' + k + 'Width']) > 0 && s['border' + k + 'Style'] !== 'none' && s['border' + k + 'Color'] !== 'rgba(0, 0, 0, 0)'; };
  const K = ['Top', 'Right', 'Bottom', 'Left'];
  const framed = (e) => K.every((k) => has(e, k)) && getComputedStyle(e).backgroundColor !== 'rgba(0, 0, 0, 0)';
  const name = (e) => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (typeof e.className === 'string' && e.className.trim() ? '.' + e.className.trim().split(/\s+/).join('.') : '');
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e)) continue;
    const r = e.getBoundingClientRect();
    for (const k of K) {
      if (!has(e, k)) continue;
      for (let a = e.parentElement; a && a !== document.body; a = a.parentElement) {
        if (!vis(a) || !has(a, k)) continue;
        const q = a.getBoundingClientRect(), d = Math.abs(r[k.toLowerCase()] - q[k.toLowerCase()]);
        if (d < 3) out.push(`double ${k.toLowerCase()} border: ${name(e)} inside ${name(a)}`);
        break;
      }
    }
    if (framed(e) && r.height > 60)
      for (let a = e.parentElement; a && a !== document.body; a = a.parentElement)
        if (vis(a) && framed(a)) { out.push(`box in a box: ${name(e)} inside ${name(a)}`); break; }
  }
  return [...new Set(out)];
})()
