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

  const carousel=document.querySelector('.related');
  if(carousel){
    const productSection=carousel.closest('section');
    const hero=document.querySelector('.hero');
    const products=[...carousel.querySelectorAll('a')];
    if(products.length<=1){
      productSection?.remove();
    }else if(productSection&&hero){
      productSection.className='product-switcher';
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
      const toolbar=document.createElement('div');
      toolbar.className='product-carousel-toolbar';
      const label=document.createElement('span');
      label.className='product-carousel-label';
      label.textContent='Другие продукты';
      toolbar.append(previous,label,next);
      carouselWrap.replaceChild(toolbar,carousel);
      previous.addEventListener('click',()=>{window.location.href=productAt(-1).href});
      next.addEventListener('click',()=>{window.location.href=productAt(1).href});
    }
  }

  const form=document.querySelector('.product-form');
  if(!form)return;

  const legacyFormUrl='/local/ajax/forms.php';
  const recaptchaKey='6LdS0yEdAAAAAOWx5cz1vJzRx5e5tufP7cn62TuA';
  const status=form.querySelector('.form-status');
  const submit=form.querySelector('[type="submit"]');
  const setStatus=(message,isError=false)=>{
    if(!status)return;
    status.textContent=message;
    status.classList.toggle('is-error',isError);
  };
  const getSessionId=async()=>{
    const response=await fetch('/',{credentials:'same-origin',cache:'no-store'});
    if(!response.ok)throw new Error('session');
    const documentMarkup=await response.text();
    const sessionDocument=new DOMParser().parseFromString(documentMarkup,'text/html');
    const sessionId=sessionDocument.querySelector('input[name="sessid"]')?.value;
    if(!sessionId)throw new Error('session');
    return sessionId;
  };
  const getRecaptchaToken=()=>new Promise((resolve,reject)=>{
    const execute=()=>window.grecaptcha.ready(()=>window.grecaptcha.execute(recaptchaKey,{action:'submit'}).then(resolve,reject));
    if(window.grecaptcha){execute();return;}
    const script=document.createElement('script');
    script.src=`https://www.google.com/recaptcha/api.js?render=${recaptchaKey}`;
    script.async=true;
    script.onload=execute;
    script.onerror=reject;
    document.head.append(script);
  });
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    if(!form.reportValidity())return;
    const product=form.dataset.product||'Фантом';
    const name=form.elements.name.value.trim();
    const phone=form.elements.phone.value.trim();
    const email=form.elements.email.value.trim();
    const company=form.elements.company.value.trim();
    const task=form.elements.task.value.trim();
    const text=[`Запрос по продукту: ${product}`,`Страница: ${window.location.href.split('#')[0]}`,company&&`Компания: ${company}`,task&&`Задача: ${task}`].filter(Boolean).join('\n');
    submit.disabled=true;
    setStatus('Отправляем заявку…');
    try{
      const [sessid,recaptcha]=await Promise.all([getSessionId(),getRecaptchaToken()]);
      const payload=new URLSearchParams({action:'faq',name,phone,email,text,privacy:'on',sessid,recaptcha});
      const response=await fetch(legacyFormUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},body:payload});
      if(!response.ok)throw new Error('submit');
      form.reset();
      setStatus('Спасибо! Заявка принята. Мы свяжемся с вами.');
    }catch(error){
      setStatus('Не удалось отправить заявку. Попробуйте ещё раз или позвоните в отдел продаж.',true);
    }finally{submit.disabled=false;}
  },true);
})();
