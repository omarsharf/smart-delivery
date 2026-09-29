
document.addEventListener('DOMContentLoaded', () => {
 
  const toggle = document.getElementById('nav-toggle');
  const links = document.getElementById('nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  
  const counters = document.querySelectorAll('.kpi .n[data-count]');
  counters.forEach(el => {
    const target = parseInt(el.getAttribute('data-count') || '0', 10);
    if (!target) { el.textContent = '0'; return; }
    let curr = 0;
    const step = Math.max(1, Math.ceil(target / 24));
    const timer = setInterval(() => {
      curr += step;
      if (curr >= target) { curr = target; clearInterval(timer); }
      el.textContent = curr.toLocaleString('ar-EG');
    }, 30);
  });

 
  const searchInput = document.getElementById('order-search');
  const table = document.getElementById('orders-table');
  const noMatch = document.getElementById('no-match');
  if (searchInput && table) {
    const rows = table.querySelectorAll('tbody tr');
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim().toLowerCase();
      let visible = 0;
      rows.forEach(r => {
        const text = r.getAttribute('data-search') || r.textContent.toLowerCase();
        const match = !q || text.includes(q);
        r.style.display = match ? '' : 'none';
        if (match) visible++;
      });
      if (noMatch) noMatch.hidden = (visible > 0 || !q);
    });
  }
});