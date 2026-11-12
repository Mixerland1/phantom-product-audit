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
    contextNav.innerHTML=`<div class="wrap"><a href="${source?'03_Готовый_вариант_Электроэнергетика.html':'electroenergetika.html'}" aria-label="Вернуться к решению «Электроэнергетика»"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 7 4 12l5 5M4 12h9a6 6 0 0 1 6 6"/></svg><span>Электроэнергетика</span></a></div>`;
    hero.insertAdjacentElement('afterend',contextNav);
  }
  const source=decodeURIComponent(location.pathname).includes('/макеты/');
  const pathname=decodeURIComponent(location.pathname);
  const homePath=source?'../публикация/предпросмотр_руководство/phantom-home.html':'phantom-home.html';
  const isCrmProduct=source
    ?pathname.endsWith('/02_Готовый_вариант_Интеграция_Фантом_и_1С_CRM.html')
    :pathname==='/'||pathname.endsWith('/index.html');
  // Keep order aligned with the local entries in assets/site-header.js > products.
  const productPages=source?[
    {path:'05_Готовый_вариант_Селективная_запись.html',name:'Селективная запись'},
    {path:'02_Готовый_вариант_Интеграция_Фантом_и_1С_CRM.html',name:'Интеграция с&nbsp;1С:CRM'}
  ]:[
    {path:'telephone-recording.html',name:'Запись телефонных переговоров'},
    {path:'dispatcher-recording.html',name:'Запись диспетчерских переговоров'},
    {path:'ip-telephony.html',name:'Запись IP-телефонии'},
    {path:'selective-recording.html',name:'Селективная запись'},
    {path:'index.html',name:'Интеграция Фантом и&nbsp;CRM'},
    {path:'pultex.html',name:'ОДС PultEx'},
    {path:'connection-schemes.html',name:'Схемы подключения МЦКРС «Фантом»'},
    {path:'phantom-cross.html',name:'Phantom Cross 5.5'}
  ];
  const servicePages=[
    {path:'personal-solutions.html',name:'Персональные решения'},
    {path:'modernization.html',name:'Комплексная модернизация'},
    {path:'training.html',name:'Обучение'}
  ];
  // Technical modules are linked beneath Phantom Cross, without expanding the global product dropdown.
  const technicalPages=[
    {path:'phantom-cross.html',name:'Phantom Cross 5.5'},
    {path:'phantom-monitoring.html',name:'Мониторинг Фантом'},
    {path:'phantom-asr.html',name:'ASR – переговоры в тексте'}
  ];
  const solutionPages=[
    {path:'atom-energy.html',name:'Атомная энергетика'},
    {path:'commercial.html',name:'Коммерческие предприятия'},
    {path:'industrial.html',name:'Промышленные предприятия'},
    {path:'auto-dealers.html',name:'Автосалоны'},
    {path:'government.html',name:'Госструктуры'},
    {path:'financial.html',name:'Финансовые организации'},
    {path:source?'03_Готовый_вариант_Электроэнергетика.html':'electroenergetika.html',name:'Электроэнергетика'},
    {path:source?'10_Готовый_вариант_Авиация_и_транспорт.html':'aviation-transport.html',name:'Авиация и\u00a0транспорт'}
  ];
  const solutionIndex=solutionPages.findIndex(page=>pathname.endsWith('/'+page.path));
  const productIndex=productPages.findIndex(page=>pathname.endsWith('/'+page.path));
  const serviceIndex=source?-1:servicePages.findIndex(page=>pathname.endsWith('/'+page.path));
  const technicalIndex=source?-1:technicalPages.findIndex(page=>pathname.endsWith('/'+page.path));
  const isTechnical=technicalIndex>0; // Cross itself retains its standard product-menu neighbors.
  const isProduct=isCrmProduct||productIndex!==-1;
  const isSolution=solutionIndex!==-1;
  const isService=serviceIndex!==-1;
  if(hero&&(isTechnical||isProduct||isSolution||isService)&&!document.querySelector('.solutions-switcher')&&!document.querySelector('.product-switcher')){
    const pages=isTechnical?technicalPages:(isProduct?productPages:(isSolution?solutionPages:servicePages));
    const currentIndex=isTechnical?technicalIndex:(isProduct?(productIndex===-1?productPages.findIndex(page=>page.path.endsWith('index.html')):productIndex):(isSolution?solutionIndex:serviceIndex));
    const navigationName=isTechnical?'Переход между техническими модулями':(isProduct?'Переход между продуктами':(isSolution?'Переход между решениями':'Переход между услугами'));
    const previousName=isTechnical?'Предыдущий модуль':(isProduct?'Предыдущий продукт':(isSolution?'Предыдущее решение':'Предыдущая услуга'));
    const nextName=isTechnical?'Следующий модуль':(isProduct?'Следующий продукт':(isSolution?'Следующее решение':'Следующая услуга'));
    const allLabel=(isTechnical||isProduct)?'Все продукты':(isSolution?'Все решения':'Все услуги');
    const allLink=(isTechnical||isProduct)?(source?homePath+'#products':'phantom-catalog.html'):(isSolution?homePath+'#industries':'https://mdis.ru/service/');
    const pageAt=offset=>pages[(currentIndex+offset+pages.length)%pages.length];
    const switcher=document.createElement('nav');
    switcher.className='solutions-switcher';
    switcher.setAttribute('aria-label',navigationName);
    switcher.innerHTML=`<div class="wrap"><div class="solutions-switcher-layout"><a class="solutions-switcher-neighbor solutions-switcher-neighbor--previous" href="${pageAt(-1).path}">${pageAt(-1).name}</a><div class="solutions-switcher-toolbar"><button class="solutions-switcher-control" type="button" aria-label="${previousName}" title="${previousName}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg></button><a class="solutions-switcher-label" href="${allLink}">${allLabel}</a><button class="solutions-switcher-control" type="button" aria-label="${nextName}" title="${nextName}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button></div><a class="solutions-switcher-neighbor solutions-switcher-neighbor--next" href="${pageAt(1).path}">${pageAt(1).name}</a></div></div>`;
    const [previous,next]=switcher.querySelectorAll('.solutions-switcher-control');
    previous.setAttribute('aria-label',`${previousName}: ${pageAt(-1).name}`);
    previous.title=`${previousName}: ${pageAt(-1).name}`;
    next.setAttribute('aria-label',`${nextName}: ${pageAt(1).name}`);
    next.title=`${nextName}: ${pageAt(1).name}`;
    previous.addEventListener('click',()=>{window.location.href=pageAt(-1).path});
    next.addEventListener('click',()=>{window.location.href=pageAt(1).path});
    hero.insertAdjacentElement('afterend',switcher);
  }
  if((document.querySelector('.context-nav')||document.querySelector('.solutions-switcher'))&&!document.getElementById('context-nav-style')){
    const style=document.createElement('style');
    style.id='context-nav-style';
    style.textContent='.context-nav,.solutions-switcher{position:relative;z-index:2;border-block:1px solid var(--line);background:var(--paper);box-shadow:0 10px 24px #2633470b}.context-nav .wrap{display:flex;align-items:center;min-height:58px}.context-nav a{display:inline-flex;align-items:center;gap:14px;color:var(--muted);font-size:10px;font-weight:900;letter-spacing:.13em;line-height:1;text-decoration:none;text-transform:uppercase}.context-nav a svg{display:grid;place-items:center;flex:0 0 42px;width:42px;height:42px;padding:10px;border:1px solid var(--line);border-radius:50%;background:var(--paper);box-shadow:0 7px 16px #26334714;fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8;transition:transform .18s,border-color .18s,background .18s,color .18s,box-shadow .18s}.context-nav a:hover,.context-nav a:focus-visible{color:var(--red);outline:none}.context-nav a:hover svg,.context-nav a:focus-visible svg{border-color:var(--red);background:var(--red);color:#fff;box-shadow:0 10px 22px #e30f2d30;transform:translateX(-2px)}.solutions-switcher .wrap{display:flex;align-items:center;min-height:58px}.solutions-switcher-layout{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;width:100%;gap:18px}.solutions-switcher-toolbar{display:flex;align-items:center;gap:14px}.solutions-switcher-neighbor{overflow:hidden;color:var(--muted);font-size:10px;font-weight:900;letter-spacing:.1em;line-height:1.15;text-decoration:none;text-transform:uppercase;white-space:nowrap;text-overflow:ellipsis}.solutions-switcher-neighbor--previous{justify-self:end;text-align:right}.solutions-switcher-neighbor--next{justify-self:start;text-align:left}.solutions-switcher-neighbor:hover,.solutions-switcher-neighbor:focus-visible,.solutions-switcher-label:hover,.solutions-switcher-label:focus-visible{color:var(--red);outline:none}.solutions-switcher-label{min-width:118px;color:var(--muted);font-size:10px;font-weight:900;letter-spacing:.13em;line-height:1;text-align:center;text-decoration:none;text-transform:uppercase}.solutions-switcher-control{display:grid;place-items:center;width:42px;height:42px;padding:0;border:1px solid var(--line);border-radius:50%;background:var(--paper);color:var(--ink);box-shadow:0 7px 16px #26334714;cursor:pointer;transition:transform .18s,border-color .18s,background .18s,color .18s}.solutions-switcher-control svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}.solutions-switcher-control:hover,.solutions-switcher-control:focus-visible{border-color:var(--red);background:var(--red);color:#fff;box-shadow:0 10px 22px #e30f2d30;outline:none}.solutions-switcher-control:first-child:hover,.solutions-switcher-control:first-child:focus-visible{transform:translateX(-2px)}.solutions-switcher-control:last-child:hover,.solutions-switcher-control:last-child:focus-visible{transform:translateX(2px)}@media(max-width:700px){.solutions-switcher-layout{gap:9px}.solutions-switcher-toolbar{gap:8px}.solutions-switcher-label{min-width:92px;font-size:9px}.solutions-switcher-neighbor{font-size:9px;letter-spacing:.07em}}@media(max-width:480px){.solutions-switcher .wrap{min-height:88px}.solutions-switcher-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);grid-template-rows:auto auto;gap:10px 12px;padding:10px 0}.solutions-switcher-toolbar{grid-column:1/-1;grid-row:1;justify-self:center}.solutions-switcher-neighbor{display:block;max-width:100%;overflow-wrap:anywhere;white-space:normal;font-size:9px;line-height:1.3}.solutions-switcher-neighbor--previous{grid-column:1;grid-row:2;justify-self:start;text-align:left}.solutions-switcher-neighbor--next{grid-column:2;grid-row:2;justify-self:end;text-align:right}}';
    document.head.appendChild(style);
  }

  const footer=document.querySelector('.footer');
  if(!footer)return;
  footer.id='site-footer';

  footer.innerHTML=`
    <div class="footer-logo-band"><div class="wrap"><div class="footer-logos" aria-label="Партнёры МДИС">
      <a href="https://mdis.ru/" aria-label="МДИС"><img src="assets/logos/mdis.svg" alt="МДИС"></a>
      <a href="${homePath}" aria-label="Фантом"><img class="footer-phantom-light" src="assets/logos/phantom-black.svg" alt="Фантом"><img class="footer-phantom-dark" src="assets/logos/phantom.svg" alt=""></a>
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
