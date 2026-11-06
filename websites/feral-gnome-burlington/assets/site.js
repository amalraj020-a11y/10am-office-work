/* Navigation enhancement for the adapted Boldo layout. No tracking or forms. */
const toggle = document.querySelector('.navbar-toggler');
const nav = document.querySelector('#site-nav');
if (toggle && nav) {
  const close = () => { nav.classList.remove('show'); toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-label', 'Open menu'); };
  toggle.addEventListener('click', () => { const open = nav.classList.toggle('show'); toggle.setAttribute('aria-expanded', String(open)); toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu'); });
  nav.querySelectorAll('a').forEach(link => link.addEventListener('click', close));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
}
