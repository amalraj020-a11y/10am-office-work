// Accessible navigation adapted from Stylish Portfolio's off-canvas interaction.
const toggle = document.querySelector('.menu-toggle');
const menu = document.querySelector('#sidebar-wrapper');
function setMenu(open) {
  menu.classList.toggle('active', open);
  menu.inert = !open;
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  toggle.textContent = open ? '×' : '☰';
}
toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', event => { if(event.key === 'Escape') { setMenu(false); toggle.focus(); } });
