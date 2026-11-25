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
    $$('[data-cmp-count]').forEach(function (n) { n.innerHTML = '<span class="vh">, picked: </span>' + picked.length; n.hidden = !picked.length; });
    var bar = $('#cmpbar'); if (bar) { bar.hidden = !picked.length; $('[data-cmp-n]', bar).textContent = picked.length; }
    var go = $('[data-cmp-go]'); if (go) go.href = root + 'compare/?c=' + picked.join(',');
    showCompare();
  }

  // The tools list: search, category, game and sort, all on the cards' own data; nothing is drawn here.
  var grid = $('#tools-grid');
  var S = { q: '', cat: '', game: '', sort: 'name' };
  // The game and category filters live in the address too (?game=…&cat=…), so a tool page's path can link to them and a
  // filtered list can be shared. A value the list doesn't offer is ignored.
  if (grid) {
    var P = new URLSearchParams(location.search);
    ['game', 'cat'].forEach(function (k) {
      var v = P.get(k), el = $('#' + k);
      if (v && el && Array.prototype.some.call(el.options, function (o) { return o.value === v; })) { S[k] = v; el.value = v; }
    });
  }
  function keepFilters() {
    var P = new URLSearchParams();
    if (S.game) P.set('game', S.game);
    if (S.cat) P.set('cat', S.cat);
    var q = P.toString(); history.replaceState(null, '', location.pathname + (q ? '?' + q : '') + location.hash);
  }
  function showTools() {
    if (!grid) return;
    var cards = $$('.card', grid), words = S.q.trim().toLowerCase().split(/\s+/).filter(Boolean), n = 0;
    cards.forEach(function (c) {
      var ok = (!S.cat || c.dataset.cat === S.cat) && (!S.game || c.dataset.game.split('|').indexOf(S.game) >= 0) &&
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

  // One status line for the page (in base.html): what a copy did is read out to screen readers too.
  function announce(w) { var s = $('#say'); if (s) { s.textContent = ''; setTimeout(function () { s.textContent = w; }, 50); } }

  // A link to an answer, a limit or an area opens the fold it sits in.
  function openTarget() {
    var id; try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; } if (!id) return;
    var el = document.getElementById(id);
    // An address from the old one-page site (#<tool>, #<card>, #compare ...) goes to its page now.
    if (!el) {
      var a = $('#addresses'), map = a ? JSON.parse(a.textContent) : {};
      var old = { compare: 'compare/', authors: 'authors/', rules: 'how/#rules', prompt: 'how/#prompt', scores: 'how/#scores' };
      var own = function (o) { return Object.prototype.hasOwnProperty.call(o, id) ? o[id] : null; };
      var to = own(map) || own(old);
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
    if (t.closest('[data-cmp-clear]')) { picked = []; store.set('compare', picked); showPicked(); return; }
    // A link to a section or an answer: it puts its address in the address bar and copies it, and leaves the page as it is
    // (a fold stays open or closed; it opens when someone follows the link).
    var anc = t.closest('a.anc, .row a.id');
    if (anc) {
      e.preventDefault();
      history.replaceState(null, '', anc.getAttribute('href'));
      var url = location.href, was = anc.title;
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () {
        anc.classList.add('done'); anc.title = 'Link copied'; announce('Link copied');
        setTimeout(function () { anc.classList.remove('done'); anc.title = was; }, 1500);
      }, function () { /* the address bar still shows the link */ });
      return;
    }
    var cp = t.closest('[data-copy]');
    if (cp) {
      var src = document.getElementById(cp.dataset.copy), text = src.textContent;
      // The button is an icon; its words (for screen readers and the tooltip) say what happened, and a tick shows it copied.
      var say = function (w) {
        cp.firstChild.textContent = w; cp.title = w; cp.classList.toggle('done', w === 'Copied'); announce(w);
        clearTimeout(cp.reset); cp.reset = setTimeout(function () { cp.firstChild.textContent = 'Copy'; cp.title = 'Copy'; cp.classList.remove('done'); }, 1500);
      };
      var sel = function () { var r = document.createRange(); r.selectNodeContents(src); var s = getSelection(); s.removeAllRanges(); s.addRange(r); say('Selected: press Ctrl+C'); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () { say('Copied'); }, sel); else sel();
    }
  });
  document.addEventListener('input', function (e) { if (e.target.id === 'q') { S.q = e.target.value; showTools(); } });
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t.id === 'sort') { S.sort = t.value; showTools(); }
    else if (t.id === 'game') { S.game = t.value; keepFilters(); showTools(); }
    else if (t.id === 'cat') { S.cat = t.value; keepFilters(); showTools(); }
    else if (t.id === 'diff') showCompare();
    else if (t.dataset.cmp) {
      picked = t.checked ? picked.concat([t.dataset.cmp]).filter(function (x, i, a) { return a.indexOf(x) === i; }) : picked.filter(function (x) { return x !== t.dataset.cmp; });
      store.set('compare', picked); showPicked();
      if ($('#cmp')) history.replaceState(null, '', '?c=' + picked.join(','));
    }
  });
  // A table too wide for the screen scrolls sideways; that one becomes a named stop for the keyboard so it can be scrolled
  // without a mouse (WCAG 2.1.1). Checked whenever a table or its frame changes size: a fold opening, fonts arriving, a resize.
  function scrollable(w) {
    if (w.scrollWidth > w.clientWidth + 1) { w.tabIndex = 0; w.setAttribute('role', 'region'); w.setAttribute('aria-label', 'Table, scrolls sideways'); }
    else { w.removeAttribute('tabindex'); w.removeAttribute('role'); w.removeAttribute('aria-label'); }
  }
  if (window.ResizeObserver) {
    var ro = new ResizeObserver(function (es) { es.forEach(function (e) { scrollable(e.target.closest('.tw')); }); });
    $$('.tw').forEach(function (w) { ro.observe(w); if (w.firstElementChild) ro.observe(w.firstElementChild); });
  }
  // A tool page: its name and score show in the sticky header while its own title is out of sight.
  var here = $('[data-here]'), h1 = $('.thead h1');
  if (here && h1 && window.IntersectionObserver) {
    new IntersectionObserver(function (es) { here.hidden = es[0].isIntersecting || es[0].boundingClientRect.top > 0; }).observe(h1);
  }
  window.addEventListener('hashchange', openTarget);
  showPicked(); showTools(); openTarget();
})();
