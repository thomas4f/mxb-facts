// MXB Facts: the little the pages need a script for. Every page reads in full without it; the script only filters, sorts,
// folds and remembers, and never draws a mark, a cost or a score (those come from the feed, through the templates).
(function () {
  'use strict';
  var root = document.body.dataset.root || '';
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode: it just isn't remembered */ } }
  };
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };

  // Theme: System, Light, Dark in turn; System forgets the choice, so the page follows the computer again.
  var themes = ['system', 'light', 'dark'];
  function showTheme() {
    var t = store.get('theme-choice', 'system'), b = $('[data-theme-toggle]');
    if (t === 'system') { delete document.documentElement.dataset.theme; try { localStorage.removeItem('theme'); } catch { /* ignore */ } }
    else { document.documentElement.dataset.theme = t; try { localStorage.setItem('theme', t); } catch { /* ignore */ } }
    if (b) { b.textContent = 'Theme: ' + t[0].toUpperCase() + t.slice(1); b.setAttribute('aria-label', 'Colour theme: ' + t + '. Change it'); }
  }
  showTheme();

  // Compare: the cards picked, remembered between pages; the tools list and the Compare page share it.
  var picked = store.get('compare', []);
  var q = new URLSearchParams(location.search).get('c');
  if (q) { picked = q.split(',').filter(Boolean); store.set('compare', picked); }
  function showPicked() {
    $$('[data-cmp]').forEach(function (b) { b.checked = picked.indexOf(b.dataset.cmp) >= 0; });
    $$('[data-cmp-count]').forEach(function (n) { n.textContent = picked.length; n.hidden = !picked.length; });
    var bar = $('#cmpbar'); if (bar) { bar.hidden = !picked.length; $('[data-cmp-n]', bar).textContent = picked.length; }
    var go = $('[data-cmp-go]'); if (go) go.href = root + 'compare/?c=' + picked.join(',');
    showCompare();
  }

  // The tools list: search, category, game and sort, all on the cards' own data; nothing is drawn here.
  var grid = $('#tools-grid');
  var S = { q: '', cat: '', game: '', sort: 'name' };
  function showTools() {
    if (!grid) return;
    var cards = $$('.card', grid), words = S.q.trim().toLowerCase().split(/\s+/).filter(Boolean), n = 0;
    cards.forEach(function (c) {
      var ok = (!S.cat || c.dataset.cat === S.cat) && (!S.game || c.dataset.game === S.game) &&
        words.every(function (w) { return c.dataset.search.indexOf(w) >= 0; });
      c.hidden = !ok; if (ok) n++;
    });
    var num = function (c) { return c.dataset.score === '' ? -1 : +c.dataset.score; };
    var by = {
      name: function (a, b) { return a.dataset.name.localeCompare(b.dataset.name); },
      score: function (a, b) { return num(b) - num(a) || by.name(a, b); },
      'score-lo': function (a, b) { return (num(a) < 0) - (num(b) < 0) || num(a) - num(b) || by.name(a, b); },
      date: function (a, b) { return b.dataset.date.localeCompare(a.dataset.date) || by.name(a, b); }
    };
    cards.sort(by[S.sort]).forEach(function (c) { grid.appendChild(c); });
    $('#count').textContent = n + ' of ' + cards.length + ' tools';
    $('#none').hidden = n > 0;
    $$('[data-pick-cat]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.pickCat === S.cat)); });
  }

  // Compare: show the picked columns, and with "Show only differences" only the rows where they differ.
  function showCompare() {
    var t = $('#cmp'); if (!t) return;
    t.classList.remove('all');
    var on = picked.slice();
    $$('[data-c]', t).forEach(function (c) { c.classList.toggle('on', on.indexOf(c.dataset.c) >= 0); });
    var diff = $('#diff') && $('#diff').checked;
    $$('tbody tr', t).forEach(function (r) {
      if (r.classList.contains('grp')) return;
      var ks = $$('td.on', r).map(function (c) { return c.dataset.k; });
      r.classList.toggle('same', diff && ks.length > 1 && ks.every(function (k) { return k === ks[0]; }));
    });
    // A tool's earlier releases show in the picker while one of its releases is picked.
    $$('.chip.older').forEach(function (c) { c.classList.toggle('show', !!$('input:checked', c) || on.length > 0); });
    var hint = $('[data-cmp-hint]'); if (hint) hint.hidden = on.length >= 2;
    var lab = $('[data-cmp-n-label]'); if (lab) lab.textContent = on.length ? '· ' + on.length + ' picked' : '';
    t.hidden = on.length < 2;
    // With tools already picked (a shared ?c= link, or picks from the tools list), the picker starts folded so the table shows first.
    var pk = $('#picker'); if (pk && !pk.dataset.seen) { pk.dataset.seen = '1'; if (on.length >= 2) pk.open = false; }
  }

  // A link to an answer, a limit or an area opens the fold it sits in.
  function openTarget() {
    var id = decodeURIComponent(location.hash.slice(1)); if (!id) return;
    var el = document.getElementById(id);
    // An address from the old one-page site (#<tool>, #<card>, #compare ...) goes to its page now.
    if (!el) {
      var a = $('#addresses'), map = a ? JSON.parse(a.textContent) : {};
      var old = { compare: 'compare/', authors: 'authors/', rules: 'how/#rules', prompt: 'how/#prompt', scores: 'how/#scores' };
      var to = map[id] || old[id];
      if (to) location.replace(root + to);
      return;
    }
    for (var d = el.closest('details'); d; d = d.parentElement && d.parentElement.closest('details')) d.open = true;
    if (el.tagName === 'DETAILS') el.open = true;
    el.scrollIntoView({ block: 'start' });
  }

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t.closest('[data-theme-toggle]')) { var c = store.get('theme-choice', 'system'); store.set('theme-choice', themes[(themes.indexOf(c) + 1) % 3]); showTheme(); return; }
    var m = t.closest('[data-more]');
    if (m) {
      var open = m.getAttribute('aria-expanded') !== 'true';
      $$('.tag[data-extra], .tag[hidden]', m.parentNode).forEach(function (x) { x.dataset.extra = '1'; x.hidden = !open; });
      m.setAttribute('aria-expanded', String(open));
      m.firstChild.textContent = open ? 'Fewer' : m.dataset.label;
      return;
    }
    var cat = t.closest('[data-pick-cat]'); if (cat) { S.cat = cat.dataset.pickCat; showTools(); return; }
    if (t.closest('[data-cmp-clear]')) { picked = []; store.set('compare', picked); showPicked(); return; }
    var cp = t.closest('[data-copy]');
    if (cp) {
      var src = document.getElementById(cp.dataset.copy), text = src.textContent;
      var sel = function () { var r = document.createRange(); r.selectNodeContents(src); var s = getSelection(); s.removeAllRanges(); s.addRange(r); cp.textContent = 'Selected'; };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () { cp.textContent = 'Copied'; }, sel); else sel();
    }
  });
  document.addEventListener('input', function (e) { if (e.target.id === 'q') { S.q = e.target.value; showTools(); } });
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t.id === 'sort') { S.sort = t.value; showTools(); }
    else if (t.id === 'game') { S.game = t.value; showTools(); }
    else if (t.id === 'diff') showCompare();
    else if (t.dataset.cmp) {
      picked = t.checked ? picked.concat([t.dataset.cmp]).filter(function (x, i, a) { return a.indexOf(x) === i; }) : picked.filter(function (x) { return x !== t.dataset.cmp; });
      store.set('compare', picked); showPicked();
      if ($('#cmp')) history.replaceState(null, '', '?c=' + picked.join(','));
    }
  });
  window.addEventListener('hashchange', openTarget);
  showPicked(); showTools(); openTarget();
})();
