(()=>{
  const root=document.documentElement;
  const theme=document.getElementById('theme');
  if(theme)theme.addEventListener('click',()=>{
    const dark=root.dataset.theme!=="dark";
    root.dataset.theme=dark?"dark":"light";
    theme.textContent=dark?"Светлая тема":"Тёмная тема";
  });

  const menu=document.querySelector('.mobile-menu');
  if(menu)document.addEventListener('click',event=>{
    if(!menu.contains(event.target))menu.removeAttribute('open');
  });

  const carousel=document.querySelector('.related');
  if(carousel){
    const productSection=carousel.closest('section');
    const hero=document.querySelector('.hero');
    const products=[...carousel.querySelectorAll('a')];
    if(products.length<=1){
      productSection?.remove();
    }else if(productSection&&hero){
      productSection.className='product-switcher';
      productSection.id='product-navigation';
      productSection.setAttribute('role','navigation');
      productSection.setAttribute('aria-label','Переход между продуктами Phantom');
      productSection.querySelector('.section-head')?.remove();
      hero.insertAdjacentElement('afterend',productSection);
      let currentIndex=products.findIndex(product=>product.getAttribute('aria-current')==='page');
      if(currentIndex<0)currentIndex=products.findIndex(product=>new URL(product.href,window.location.href).pathname===window.location.pathname);
      if(currentIndex<0)currentIndex=0;
      const productName=product=>[product.querySelector('b')?.textContent.trim(),product.querySelector('small')?.textContent.trim()].filter(Boolean).join(', ')||product.textContent.replace(/\s+/g,' ').trim();
      const productAt=offset=>products[(currentIndex+offset+products.length)%products.length];

      const previous=document.createElement('button');
      previous.className='product-carousel-control';
      previous.type='button';
      previous.setAttribute('aria-label',`Предыдущий продукт: ${productName(productAt(-1))}`);
      previous.title=`Предыдущий продукт: ${productName(productAt(-1))}`;
      previous.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>';
      const next=document.createElement('button');
      next.className='product-carousel-control';
      next.type='button';
      next.setAttribute('aria-label',`Следующий продукт: ${productName(productAt(1))}`);
      next.title=`Следующий продукт: ${productName(productAt(1))}`;
      next.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
      const carouselWrap=carousel.parentNode;
      const productNavigation=document.createElement('div');
      productNavigation.className='product-switcher-row';
      const parentLink=document.createElement('a');
      parentLink.className='product-parent-link';
      parentLink.href=decodeURIComponent(location.pathname).includes('/макеты/')?'03_Готовый_вариант_Электроэнергетика.html':'electroenergetika.html';
      parentLink.setAttribute('aria-label','Вернуться к решению «Электроэнергетика»');
      parentLink.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 7 4 12l5 5M4 12h9a6 6 0 0 1 6 6"/></svg><span>Электроэнергетика</span>';
      const nextSectionLink=document.createElement('a');
      nextSectionLink.className='product-next-link';
      nextSectionLink.href='https://mdis.ru/solution/transprot/';
      nextSectionLink.setAttribute('aria-label','Перейти к решению «Авиация и транспорт»');
      nextSectionLink.innerHTML='<span>Авиация и транспорт</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 7 5 5-5 5M20 12h-9a6 6 0 0 0-6 6"/></svg>';
      const toolbar=document.createElement('div');
      toolbar.className='product-carousel-toolbar';
      const label=document.createElement('span');
      label.className='product-carousel-label';
      label.textContent='Другие продукты';
      toolbar.append(previous,label,next);
      productNavigation.append(parentLink,toolbar,nextSectionLink);
      carouselWrap.replaceChild(productNavigation,carousel);
      const goToProduct=product=>{
        const target=new URL(product.href,window.location.href);
        target.hash='product-navigation';
        window.location.href=target.href;
      };
      previous.addEventListener('click',()=>{goToProduct(productAt(-1))});
      next.addEventListener('click',()=>{goToProduct(productAt(1))});
      if(location.hash==='#product-navigation'){
        requestAnimationFrame(()=>{
          const headerHeight=document.querySelector('.header')?.getBoundingClientRect().height||0;
          const top=productSection.getBoundingClientRect().top+window.scrollY-headerHeight;
          window.scrollTo({top:Math.max(0,top),behavior:'auto'});
        });
      }
    }
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
