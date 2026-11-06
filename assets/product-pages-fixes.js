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
    carousel.classList.add('product-carousel');
    carousel.setAttribute('role','region');
    carousel.setAttribute('aria-label','Другие продукты Phantom');

    const current=[...carousel.querySelectorAll('a')].find(link=>link.querySelector('span')?.textContent.trim()==='Текущий');
    if(current)current.setAttribute('aria-current','page');

    const controls=document.createElement('div');
    controls.className='product-carousel-controls';
    controls.setAttribute('aria-label','Прокрутка списка продуктов');
    const hint=document.createElement('p');
    hint.className='product-carousel-hint';
    hint.textContent='Листайте карточки или используйте кнопки';
    const actions=document.createElement('div');
    actions.className='product-carousel-actions';
    const previous=document.createElement('button');
    previous.className='product-carousel-control';
    previous.type='button';
    previous.setAttribute('aria-label','Предыдущие продукты');
    previous.textContent='← Предыдущий продукт';
    const next=document.createElement('button');
    next.className='product-carousel-control';
    next.type='button';
    next.setAttribute('aria-label','Следующие продукты');
    next.textContent='Следующий продукт →';
    actions.append(previous,next);
    controls.append(hint,actions);
    carousel.parentNode.insertBefore(controls,carousel);

    const updateControls=()=>{
      const max=Math.max(0,carousel.scrollWidth-carousel.clientWidth);
      previous.disabled=carousel.scrollLeft<=1;
      next.disabled=carousel.scrollLeft>=max-1;
    };
    const scrollProducts=direction=>carousel.scrollBy({left:direction*Math.max(240,carousel.clientWidth*.7),behavior:'smooth'});
    previous.addEventListener('click',()=>scrollProducts(-1));
    next.addEventListener('click',()=>scrollProducts(1));
    carousel.addEventListener('scroll',updateControls,{passive:true});
    window.addEventListener('resize',updateControls);
    requestAnimationFrame(updateControls);
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
