'use strict';
const button=document.querySelector('.navbar-toggle');
const menu=document.querySelector('#custom-collapse');
function closeMenu(){menu.classList.remove('open');button.setAttribute('aria-expanded','false');}
button.addEventListener('click',()=>{const opened=menu.classList.toggle('open');button.setAttribute('aria-expanded',String(opened));});
menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});
