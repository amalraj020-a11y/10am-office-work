'use strict';
const button=document.querySelector('.navbar-toggler');
const menu=document.getElementById('navbarResponsive');
function closeMenu(){menu.classList.remove('show');button.setAttribute('aria-expanded','false');}
button.addEventListener('click',()=>{const open=button.getAttribute('aria-expanded')!=='true';menu.classList.toggle('show',open);button.setAttribute('aria-expanded',String(open));});
menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeMenu();}});
