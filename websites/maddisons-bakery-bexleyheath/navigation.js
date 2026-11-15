// Responsive navigation adapted for the MIT-licensed Resume sidebar structure.
const button=document.querySelector('.navbar-toggler');
const menu=document.getElementById('navbarResponsive');
button.addEventListener('click',()=>{const open=button.getAttribute('aria-expanded')!=='true';button.setAttribute('aria-expanded',String(open));menu.classList.toggle('show',open);});
menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{button.setAttribute('aria-expanded','false');menu.classList.remove('show');}));
