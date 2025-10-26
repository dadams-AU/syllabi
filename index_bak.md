---
title: Adams Syllabi Collection
layout: null
---

<div id="readme-root">
{% capture readme %}{% include_relative README.md %}{% endcapture %}
{{ readme | markdownify }}
</div>

<style>
  /* Minimal, framework-free styling */
  .syllabi-controls { display:flex; gap:.75rem; align-items:center; margin:1rem 0; flex-wrap:wrap; }
  .syllabi-input, .syllabi-select { padding:.6rem; border:1px solid #d1d5db; border-radius:.5rem; }
  .syllabi-input { flex:1 1 280px; }
  .syllabi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:1rem; }
  .syllabi-card { display:block; padding:1rem; border:1px solid #e5e7eb; border-radius:.75rem; text-decoration:none; color:inherit; background:#fff; }
  .syllabi-card:hover { box-shadow:0 2px 12px rgba(0,0,0,.06); }
  .syllabi-title { font-weight:600; margin-bottom:.25rem; }
  .syllabi-meta { font-size:.9rem; color:#6b7280; }
  @media (prefers-color-scheme: dark) {
    .syllabi-input, .syllabi-select { border-color:#374151; background:#111827; color:#e5e7eb; }
    .syllabi-card { background:#0b1220; border-color:#1f2937; }
    .syllabi-card:hover { box-shadow:0 2px 12px rgba(255,255,255,.06); }
    .syllabi-meta { color:#9ca3af; }
  }
</style>

<script>
(function () {
  const root = document.getElementById('readme-root');
  if (!root) return;

  // 1) Find the section headed “Available Syllabi”
  const headings = [...root.querySelectorAll('h2, h3, h4')];
  const availableIdx = headings.findIndex(h => /available syllabi/i.test(h.textContent));
  if (availableIdx === -1) return;

  // Collect all <ul> lists until the next H2/H3 (end of section)
  const uls = [];
  for (let el = headings[availableIdx].nextElementSibling; el; el = el.nextElementSibling) {
    if (/^H[23]$/.test(el.tagName)) break;
    if (el.tagName === 'UL') uls.push(el);
  }
  const links = uls.flatMap(ul => [...ul.querySelectorAll('a')]);

  if (!links.length) return;

  // Extract a reasonable course code and short title from the anchor text / href
  function extractCourseCodeAndTitle(a) {
    const title = a.textContent.replace(/\s+/g, ' ').trim();
    // Try to pull a course code like "POSC 315", "CRJU 320", "POSC/CRJU 320", "POSC 521"
    const codeMatch = title.match(/\b(?:POSC|CRJU)(?:\/POSC|\/CRJU)?\s*\d{3}\b/i)
                  || a.href.match(/\b(?:POSC|CRJU)(?:_POSC|_CRJU)?\s*%20?\d{3}\b/i)
                  || a.href.match(/\b(?:POSC|CRJU)\s*\d{3}\b/i);
    const code = codeMatch ? codeMatch[0].replace(/%20/g,' ').replace(/_/g,' ').toUpperCase() : '';

    // Strip the code from the display title if it’s at the start
    let cleanTitle = title;
    if (code && cleanTitle.toUpperCase().startsWith(code)) {
      cleanTitle = cleanTitle.slice(code.length).replace(/^[\s:–-]+/, '');
    }
    return { code, title: cleanTitle || title };
  }

  const items = links.map(a => {
    const { code, title } = extractCourseCodeAndTitle(a);
    return {
      title,
      code,
      href: a.href,
      rawTitle: a.textContent.replace(/\s+/g,' ').trim()
    };
  });

  // 2) Build UI shell
  const controls = document.createElement('div');
  controls.className = 'syllabi-controls';
  controls.innerHTML = `
    <input id="syllabi-search" class="syllabi-input" type="search" placeholder="Search by course code or title…" aria-label="Search syllabi">
    <select id="syllabi-sort" class="syllabi-select" aria-label="Sort syllabi">
      <option value="code">Sort: Course Code</option>
      <option value="title">Sort: Title</option>
    </select>
  `;

  const grid = document.createElement('div');
  grid.id = 'syllabi-grid';
  grid.className = 'syllabi-grid';

  // Insert the controls + grid just above the Available Syllabi heading
  const anchor = headings[availableIdx];
  anchor.parentNode.insertBefore(controls, anchor);
  anchor.parentNode.insertBefore(grid, anchor);

  // 3) Render cards
  function render(list) {
    grid.innerHTML = '';
    list.forEach(({ title, href, code }) => {
      const a = document.createElement('a');
      a.className = 'syllabi-card';
      a.href = href;
      a.innerHTML = `
        <div class="syllabi-title">${title}</div>
        <div class="syllabi-meta">${code || 'Course'}</div>
      `;
      grid.appendChild(a);
    });
  }

  // 4) Filtering/sorting
  const search = controls.querySelector('#syllabi-search');
  const sortSel = controls.querySelector('#syllabi-sort');

  function apply() {
    const q = (search.value || '').toLowerCase();
    const sorted = [...items].sort((a, b) => {
      if (sortSel.value === 'title') return a.title.localeCompare(b.title, undefined, { numeric: true });
      // default: sort by code, then title
      const c = (a.code || '').localeCompare((b.code || ''), undefined, { numeric: true });
      return c !== 0 ? c : a.title.localeCompare(b.title, undefined, { numeric: true });
    });
    const filtered = sorted.filter(x =>
      (x.title + ' ' + x.code + ' ' + x.rawTitle).toLowerCase().includes(q)
    );
    render(filtered);
  }

  search.addEventListener('input', apply);
  sortSel.addEventListener('change', apply);
  apply();

  // 5) Progressive enhancement: keep the original lists for accessibility,
  // but collapse them into a <details> so the cards are primary.
  const wrapper = document.createElement('details');
  wrapper.style.marginTop = '1rem';
  const summary = document.createElement('summary');
  summary.textContent = 'Show original syllabus lists';
  wrapper.appendChild(summary);
  uls.forEach(ul => wrapper.appendChild(ul));
  // Insert wrapper right after the grid
  grid.parentNode.insertBefore(wrapper, grid.nextSibling);
})();
</script>
