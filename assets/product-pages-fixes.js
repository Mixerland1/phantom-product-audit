(()=>{
  const root=document.documentElement;
  const theme=document.getElementById('theme');
  if(theme)theme.addEventListener('click',()=>{
    const dark=root.dataset.theme!=="dark";
    root.dataset.theme=dark?"dark":"light";
    theme.textContent=dark?"Светлая тема":"Тёмная тема";
  });

  const menu=document.querySelector('.mobile-menu');
  if(menu){
    document.addEventListener('click',event=>{
      if(!menu.contains(event.target))menu.removeAttribute('open');
    });
    menu.querySelectorAll('a[href^="#"]').forEach(link=>link.addEventListener('click',()=>{
      menu.removeAttribute('open');
    }));
  }

  const form=document.querySelector('.product-form');
  if(!form)return;
  form.addEventListener('submit',event=>{
    event.preventDefault();
    const lines=[...form.querySelectorAll('input,textarea')].map(field=>{
      const value=field.value.trim();
      if(!value)return '';
      const label=form.querySelector(`label[for="${field.id}"]`);
      return `${label?label.textContent.replace(/\s+/g,' ').trim():field.name}: ${value}`;
    }).filter(Boolean);
    const subject=form.dataset.subject||'Запрос по продукту «Фантом»';
    window.location.href=`mailto:sales@mdis.ru?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(['Здравствуйте!',...lines].join('\n'))}`;
  },true);
})();
