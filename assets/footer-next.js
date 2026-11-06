(()=>{
  const brand=document.querySelector('.header .brand');
  if(brand){
    brand.setAttribute('aria-label','Фантом');
    brand.innerHTML='<img class="brand-logo-light" src="assets/logos/phantom-black.svg" alt="Фантом"><img class="brand-logo-dark" src="assets/logos/phantom.svg" alt="">';
  }

  const hero=document.querySelector('.hero');
  const sectionLink=document.querySelector('.hero .crumb a[href*="electroenergetika"]');
  const drilldownPage=/\/(?:selective-recording|attestation-fsk-ees)\.html$/.test(location.pathname);
  if(drilldownPage&&hero&&sectionLink&&!document.querySelector('.context-nav')){
    const contextNav=document.createElement('nav');
    contextNav.className='context-nav';
    contextNav.setAttribute('aria-label','Навигация по разделу');
    const source=decodeURIComponent(location.pathname).includes('/макеты/');
    contextNav.innerHTML=`<div class="wrap"><a href="${source?'03_Готовый_вариант_Электроэнергетика.html':'/electroenergetika.html'}">К решению для электроэнергетики</a></div>`;
    hero.insertAdjacentElement('afterend',contextNav);
  }
  const source=decodeURIComponent(location.pathname).includes('/макеты/');
  const solutionPages=source?[
    {path:'02_Готовый_вариант_Интеграция_Фантом_и_1С_CRM.html',name:'Интеграция с 1С:CRM'},
    {path:'03_Готовый_вариант_Электроэнергетика.html',name:'Электроэнергетика'}
  ]:[
    {path:'index.html',name:'Интеграция с 1С:CRM'},
    {path:'electroenergetika.html',name:'Электроэнергетика'}
  ];
  const pathname=decodeURIComponent(location.pathname);
  let solutionIndex=solutionPages.findIndex(solution=>pathname.endsWith(`/${solution.path}`));
  if(!source&&pathname==='/')solutionIndex=0;
  if(hero&&solutionIndex>=0&&!document.querySelector('.solutions-switcher')){
    const solutionAt=offset=>solutionPages[(solutionIndex+offset+solutionPages.length)%solutionPages.length];
    const switcher=document.createElement('nav');
    switcher.className='solutions-switcher';
    switcher.setAttribute('aria-label','Переход между решениями');
    switcher.innerHTML='<div class="wrap"><div class="solutions-switcher-toolbar"><button class="solutions-switcher-control" type="button" aria-label="Предыдущее решение" title="Предыдущее решение"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg></button><span class="solutions-switcher-label">Все решения</span><button class="solutions-switcher-control" type="button" aria-label="Следующее решение" title="Следующее решение"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button></div></div>';
    const [previous,next]=switcher.querySelectorAll('.solutions-switcher-control');
    previous.setAttribute('aria-label',`Предыдущее решение: ${solutionAt(-1).name}`);
    previous.title=`Предыдущее решение: ${solutionAt(-1).name}`;
    next.setAttribute('aria-label',`Следующее решение: ${solutionAt(1).name}`);
    next.title=`Следующее решение: ${solutionAt(1).name}`;
    previous.addEventListener('click',()=>{window.location.href=solutionAt(-1).path});
    next.addEventListener('click',()=>{window.location.href=solutionAt(1).path});
    hero.insertAdjacentElement('afterend',switcher);
  }
  if((document.querySelector('.context-nav')||document.querySelector('.solutions-switcher'))&&!document.getElementById('context-nav-style')){
    const style=document.createElement('style');
    style.id='context-nav-style';
    style.textContent='.context-nav,.solutions-switcher{position:relative;z-index:2;border-block:1px solid var(--line);background:var(--paper);box-shadow:0 10px 24px #2633470b}.context-nav .wrap{display:flex;align-items:center;min-height:58px}.context-nav a{display:inline-flex;align-items:center;gap:10px;color:var(--ink);font-size:12px;font-weight:900;text-decoration:none}.context-nav a:before{content:"←";display:grid;place-items:center;width:28px;height:28px;border:1px solid var(--line);border-radius:50%;font-size:17px;font-weight:400;transition:transform .18s,border-color .18s,background .18s,color .18s}.context-nav a:hover:before,.context-nav a:focus-visible:before{border-color:var(--red);background:var(--red);color:#fff;transform:translateX(-2px)}.solutions-switcher .wrap{display:flex;align-items:center;justify-content:center;min-height:58px}.solutions-switcher-toolbar{display:flex;align-items:center;gap:14px}.solutions-switcher-label{min-width:118px;color:var(--muted);font-size:10px;font-weight:900;letter-spacing:.13em;line-height:1;text-align:center;text-transform:uppercase}.solutions-switcher-control{display:grid;place-items:center;width:42px;height:42px;padding:0;border:1px solid var(--line);border-radius:50%;background:var(--paper);color:var(--ink);box-shadow:0 7px 16px #26334714;cursor:pointer;transition:transform .18s,border-color .18s,background .18s,color .18s}.solutions-switcher-control svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}.solutions-switcher-control:hover,.solutions-switcher-control:focus-visible{border-color:var(--red);background:var(--red);color:#fff;box-shadow:0 10px 22px #e30f2d30;outline:none}.solutions-switcher-control:first-child:hover,.solutions-switcher-control:first-child:focus-visible{transform:translateX(-2px)}.solutions-switcher-control:last-child:hover,.solutions-switcher-control:last-child:focus-visible{transform:translateX(2px)}';
    document.head.appendChild(style);
  }

  const footer=document.querySelector('.footer');
  if(!footer)return;
  footer.id='site-footer';

  footer.innerHTML=`
    <div class="footer-logo-band"><div class="wrap"><div class="footer-logos" aria-label="Партнёры МДИС">
      <a href="/" aria-label="МДИС"><img src="assets/logos/mdis.svg" alt="МДИС"></a>
      <a href="/" aria-label="Фантом"><img class="footer-phantom-light" src="assets/logos/phantom-black.svg" alt="Фантом"><img class="footer-phantom-dark" src="assets/logos/phantom.svg" alt=""></a>
      <a href="https://granulex.ru/" target="_blank" rel="noopener" aria-label="Granulex"><img src="assets/logos/granulex.svg" alt="Granulex"></a>
      <a class="footer-pultex" href="https://pultex.pro/" target="_blank" rel="noopener" aria-label="PultEx"><img class="footer-pultex-color" src="assets/logos/pultex.svg" alt="PultEx"><img class="footer-pultex-white" src="assets/logos/pultex-white.svg" alt=""></a>
    </div></div></div>
    <div class="footer-contact-zone">
      <div class="footer-map" aria-hidden="true"><img src="assets/map2.0b139232.png" alt=""><div class="footer-pin"><i></i><i></i><i></i><b></b></div></div>
      <div class="wrap footer-in footer-next">
      <div class="footer-details"><b>ООО «МДИС»</b><address>123022, Россия, г. Москва, ул. 1905 года, д. 7, стр. 1</address><a class="footer-general-phone" href="tel:+74957833379">+7 (495) 783-33-79</a></div>
      <div class="footer-channel"><b>Отдел продаж</b><a href="mailto:sales@mdis.ru">sales@mdis.ru</a></div>
      <div class="footer-channel footer-support"><b>Техническая поддержка</b><a href="mailto:support@mdis.ru">support@mdis.ru</a><span class="footer-legal"><a href="https://mdis.ru/privacy-policy/" target="_blank" rel="noopener">Конфиденциальность</a><a href="https://mdis.ru/cookie-policy/" target="_blank" rel="noopener">Cookie</a></span></div>
      </div>
    </div>`;

  const setTheme=()=>{
    const color=getComputedStyle(footer).backgroundColor.match(/\d+/g);
    if(!color)return;
    const [r,g,b]=color.map(Number);
    footer.classList.toggle('footer--dark',(r*299+g*587+b*114)/1000<145);
  };
  setTheme();
  new MutationObserver(()=>requestAnimationFrame(setTheme)).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme','class']});
})();
