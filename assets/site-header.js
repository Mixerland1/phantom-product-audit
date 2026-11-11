(()=>{
  const header=document.querySelector('.header');
  if(!header)return;

  const pathname=decodeURIComponent(location.pathname);
  const source=pathname.includes('/макеты/');
  const localPreview=location.protocol==='file:'&&pathname.includes('/предпросмотр_руководство/');
  const page=(sourceName,previewName,liveName)=>source?sourceName:(localPreview?previewName:liveName);
  const paths={
    home:page('../публикация/предпросмотр_руководство/phantom-home.html','phantom-home.html','phantom-home.html'),
    crm:page('02_Готовый_вариант_Интеграция_Фантом_и_1С_CRM.html','index.html','index.html'),
    atom:page('atom-energy.html','atom-energy.html','atom-energy.html'),
    commercial:page('commercial.html','commercial.html','commercial.html'),
    industrial:page('industrial.html','industrial.html','industrial.html'),
    government:page('government.html','government.html','government.html'),
    financial:page('financial.html','financial.html','financial.html'),
    autoDealers:page('auto-dealers.html','auto-dealers.html','auto-dealers.html'),
    catalog:page('phantom-catalog.html','phantom-catalog.html','phantom-catalog.html'),
    ipTelephony:page('ip-telephony.html','ip-telephony.html','ip-telephony.html'),
    electro:page('03_Готовый_вариант_Электроэнергетика.html','electroenergetika.html','electroenergetika.html'),
    aviation:page('10_Готовый_вариант_Авиация_и_транспорт.html','aviation-transport.html','aviation-transport.html'),
    selective:page('05_Готовый_вариант_Селективная_запись.html','selective-recording.html','selective-recording.html'),
    pro5:page('06_Phantom_Pro_уровень_5.html','phantom-pro-level-5.html','phantom-pro-level-5.html'),
    pro6:page('07_Phantom_Pro_уровень_6.html','phantom-pro-level-6.html','phantom-pro-level-6.html'),
    pc2:page('08_Phantom_PC_2.html','phantom-pc-2.html','phantom-pc-2.html'),
    ultra:page('09_Фантом_Ультра.html','phantom-ultra.html','phantom-ultra.html'),
    aviaton:page('11_Готовый_вариант_Авиатон.html','aviaton.html','aviaton.html')
  };
  const solutions=[
    {label:'Атомная энергетика',href:paths.atom},
    {label:'Коммерческие предприятия',href:paths.commercial},
    {label:'Промышленные предприятия',href:paths.industrial},
    {label:'Автосалоны',href:paths.autoDealers},
    {label:'Госструктуры',href:paths.government},
    {label:'Финансовые организации',href:paths.financial},
    {label:'Электроэнергетика',href:paths.electro},
    {label:'Авиация и\u00a0транспорт',href:paths.aviation},
    {label:'Персональные решения',href:'https://mdis.ru/service/personalnye-resheniya/'}
  ];
  const products=[
    {label:'Запись телефонных переговоров',href:paths.catalog+'#telephone-recording'},
    {label:'Запись диспетчерских переговоров',href:paths.catalog+'#dispatcher-recording'},
    {label:'Запись IP-телефонии',href:paths.ipTelephony},
    {label:'Селективная запись',href:paths.selective},
    {label:'Интеграция Фантом и\u00a0CRM',href:paths.crm},
    {label:'ОДС PultEx',href:'https://mdis.ru/catalog/ods-pulteks/'},
    {label:'Схемы подключения МЦКРС «Фантом»',href:'https://mdis.ru/catalog/'},
    {label:'Granulex',href:'https://granulex.ru/'}
  ];
  const cards=list=>list.map(item=>`<a class="site-menu-card" href="${item.href}">${item.label}<b aria-hidden="true">↗</b></a>`).join('');
  const desktopMenu=(label,list,allHref,allLabel)=>`<details class="site-menu"><summary>${label}<i aria-hidden="true"></i></summary><section class="site-menu-panel"><div class="site-menu-list">${cards(list)}</div><a class="site-menu-all" href="${allHref}">${allLabel}<b aria-hidden="true">→</b></a></section></details>`;
  const mobileMenu=(label,list,allHref,allLabel)=>`<details class="site-mobile-group"><summary>${label}<i aria-hidden="true"></i></summary><div>${cards(list)}<a class="site-mobile-all" href="${allHref}">${allLabel}</a></div></details>`;
  const directLinks=[
    {label:'Услуги',href:'https://mdis.ru/service/'},
    {label:'Новости',href:'https://mdis.ru/news/'},
    {label:'Поддержка',href:'https://mdis.ru/support/'},
    {label:'Компания',href:'https://mdis.ru/about/'}
  ];
  const direct=directLinks.map(item=>`<a href="${item.href}">${item.label}</a>`).join('');
  const desktopNav=`${desktopMenu('Решения',solutions,paths.home+'#industries','О\u00a0решениях Phantom')}${desktopMenu('Продукты',products,paths.catalog,'Все продукты Phantom')}${direct}`;
  const mobileNav=`${mobileMenu('Решения',solutions,paths.home+'#industries','О\u00a0решениях Phantom')}${mobileMenu('Продукты',products,paths.catalog,'Все продукты Phantom')}${direct}`;

  header.className='header site-header';
  header.innerHTML=`<div class="wrap header-in site-header-in"><a class="brand site-brand" href="${paths.home}" aria-label="Phantom — главная"><img class="site-brand-logo" src="assets/logos/phantom-black.svg" alt="Phantom"></a><nav class="nav site-nav" aria-label="Основная навигация">${desktopNav}</nav><button class="site-theme-toggle" id="theme-toggle" type="button" aria-label="Переключить цветовую тему"></button><details class="mobile-menu site-mobile-menu"><summary aria-label="Открыть меню"></summary><nav class="site-mobile-popover" aria-label="Основная навигация">${mobileNav}</nav></details></div>`;

  const currentPath=decodeURIComponent(location.pathname).replace(/\/+$/,'');
  const isCurrent=item=>{try{const url=new URL(item.href,location.href);return url.origin===location.origin&&decodeURIComponent(url.pathname).replace(/\/+$/,'')===currentPath}catch(error){return false}};
  const currentGroup=solutions.some(isCurrent)?0:(products.some(isCurrent)?1:-1);
  if(currentGroup>=0){
    const desktopGroups=header.querySelectorAll('.site-menu');
    const mobileGroups=header.querySelectorAll('.site-mobile-group');
    desktopGroups[currentGroup]?.classList.add('site-menu--current');
    desktopGroups[currentGroup]?.querySelector('summary')?.setAttribute('aria-current','page');
    mobileGroups[currentGroup]?.classList.add('site-mobile-group--current');
  }

  const mobile=header.querySelector('.site-mobile-menu');
  const themeToggle=header.querySelector('.site-theme-toggle');
  const renderTheme=()=>{
    const dark=document.documentElement.dataset.theme==='dark';
    themeToggle.innerHTML=dark
      ?'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
      :'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
    themeToggle.setAttribute('aria-label',dark?'Переключить на светлую тему':'Переключить на тёмную тему');
    themeToggle.title=dark?'Светлая тема':'Тёмная тема';
    themeToggle.setAttribute('aria-pressed',String(dark));
  };
  themeToggle.addEventListener('click',()=>{
    document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';
    try{localStorage.setItem('mdis-theme',document.documentElement.dataset.theme)}catch(error){}
    renderTheme();
  });
  renderTheme();
  document.addEventListener('click',event=>{
    if(mobile&&!mobile.contains(event.target))mobile.removeAttribute('open');
    header.querySelectorAll('.site-menu[open]').forEach(menu=>{if(!menu.contains(event.target))menu.removeAttribute('open')});
  });

  if(document.getElementById('site-header-style'))return;
  const style=document.createElement('style');
  style.id='site-header-style';
  style.textContent=`
    :root{--site-header-height:64px}
    .site-header{position:sticky;top:0;z-index:30;border-bottom:1px solid color-mix(in srgb,var(--line) 82%,transparent);background:color-mix(in srgb,var(--paper) 97%,transparent);backdrop-filter:blur(10px) saturate(1.06)}
    .site-header .site-header-in{display:flex;align-items:center;min-height:var(--site-header-height);gap:clamp(12px,1.35vw,20px)}
    .site-header .site-brand{display:flex;flex:0 0 auto;align-items:center;margin-right:auto;text-decoration:none}
    .site-header .site-brand-logo{display:block;width:108px;height:auto}
    .site-header .site-nav{display:flex;align-items:stretch;gap:clamp(14px,1.25vw,20px);margin-left:0;color:var(--muted);font-size:13px;font-weight:600}
    .site-header .site-nav>a,.site-header .site-menu>summary{position:relative;display:flex;align-items:center;gap:6px;height:var(--site-header-height);padding:0;color:inherit;font:inherit;text-decoration:none;white-space:nowrap;cursor:pointer;list-style:none}
    .site-header .site-menu>summary::-webkit-details-marker{display:none}
    .site-header .site-menu>summary i{width:6px;height:6px;border-right:1.4px solid currentColor;border-bottom:1.4px solid currentColor;transform:translateY(-2px) rotate(45deg);transition:transform .18s}
    .site-header .site-menu[open]>summary i{transform:translateY(2px) rotate(225deg)}
    .site-header .site-nav>a:after,.site-header .site-menu>summary:after{position:absolute;right:0;bottom:0;left:0;height:2px;background:var(--red);content:"";opacity:0;transform:scaleX(.4);transition:opacity .18s,transform .18s}
    .site-header .site-nav>a:hover,.site-header .site-nav>a:focus-visible,.site-header .site-menu>summary:hover,.site-header .site-menu>summary:focus-visible,.site-header .site-menu[open]>summary,.site-header .site-menu--current>summary{color:var(--ink);outline:none}
    .site-header .site-nav>a:hover:after,.site-header .site-nav>a:focus-visible:after,.site-header .site-menu>summary:hover:after,.site-header .site-menu>summary:focus-visible:after,.site-header .site-menu[open]>summary:after,.site-header .site-menu--current>summary:after{opacity:1;transform:scaleX(1)}
    .site-header .site-menu{position:relative}
    .site-header .site-menu-panel{position:absolute;top:calc(var(--site-header-height) - 4px);left:-16px;width:396px;padding:12px 14px 15px;border:1px solid var(--line);border-radius:12px;background:var(--paper);box-shadow:0 18px 42px #12203620}
    .site-header .site-menu-list{display:grid;grid-template-columns:1fr 1fr;gap:4px}
    .site-header .site-menu-card{position:relative;display:flex;align-items:center;min-height:46px;padding:9px 27px 9px 10px;border:1px solid transparent;border-radius:8px;color:var(--ink);font-size:12.5px;font-weight:600;line-height:1.25;text-decoration:none;transition:border-color .18s,background .18s,color .18s}
    .site-header .site-menu-card b{position:absolute;right:10px;color:var(--red);font-size:13px}
    .site-header .site-menu-card:hover,.site-header .site-menu-card:focus-visible{border-color:var(--line);background:var(--soft);color:var(--red);outline:none}
    .site-header .site-menu-all{display:flex;align-items:center;justify-content:space-between;margin-top:9px;padding:10px 3px 0;border-top:1px solid var(--line);color:var(--ink);font-size:11.5px;font-weight:700;text-decoration:none}
    .site-header .site-menu-all b{color:var(--red);font-size:15px}.site-header .site-menu-all:hover,.site-header .site-menu-all:focus-visible{color:var(--red);outline:none}
    .site-header .site-theme-toggle{flex:0 0 auto;display:grid;place-items:center;width:36px;height:36px;padding:0;border:1px solid var(--line);border-radius:50%;background:transparent;color:var(--ink);cursor:pointer;transition:background .18s,border-color .18s,color .18s}
    .site-header .site-theme-toggle svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
    .site-header .site-theme-toggle:hover,.site-header .site-theme-toggle:focus-visible{border-color:var(--ink);background:var(--soft);outline:none}
    .site-header .site-mobile-menu{display:none!important}
    html[data-theme="dark"] .site-header .site-brand-logo{filter:invert(1) brightness(2)}
    @media(max-width:1080px){
      :root{--site-header-height:60px}
      .site-header .site-brand-logo{width:104px}
      .site-header .site-nav{display:none!important}.site-header .site-mobile-menu{position:relative;display:block!important}.site-header .site-mobile-menu>summary{display:grid;place-items:center;width:36px;height:36px;list-style:none;border:1px solid var(--line);border-radius:50%;color:var(--ink);cursor:pointer}.site-header .site-mobile-menu>summary::-webkit-details-marker{display:none}.site-header .site-mobile-menu>summary:after{content:none!important}.site-header .site-mobile-menu>summary:before{content:"☰";font-size:18px;line-height:1}.site-header .site-mobile-menu[open]>summary:before{content:"×";font-size:23px;font-weight:400}
      .site-header .site-mobile-popover{position:absolute;top:44px;right:0;display:grid;min-width:min(336px,calc(100vw - 32px));padding:6px;border:1px solid var(--line);border-radius:10px;background:var(--paper);box-shadow:0 18px 42px #12203624}.site-header .site-mobile-popover>a{display:block;padding:10px 11px;border-radius:6px;color:var(--ink);font-size:13px;font-weight:600;text-decoration:none}.site-header .site-mobile-popover>a:hover,.site-header .site-mobile-popover>a:focus-visible{background:var(--soft);color:var(--red);outline:none}
      .site-header .site-mobile-group{border-bottom:1px solid var(--line)}.site-header .site-mobile-group:last-of-type{border-bottom:0}.site-header .site-mobile-group summary{display:flex;align-items:center;justify-content:space-between;padding:10px 11px;color:var(--ink);font-size:13px;font-weight:650;cursor:pointer;list-style:none}.site-header .site-mobile-group--current>summary{color:var(--red)}.site-header .site-mobile-group summary::-webkit-details-marker{display:none}.site-header .site-mobile-group summary:before,.site-header .site-mobile-group summary:after{content:none!important}.site-header .site-mobile-group summary i{width:6px;height:6px;border-right:1.4px solid currentColor;border-bottom:1.4px solid currentColor;transform:translateY(-2px) rotate(45deg)}.site-header .site-mobile-group[open] summary i{transform:translateY(2px) rotate(225deg)}
      .site-header .site-mobile-group>div{display:grid;gap:3px;padding:0 5px 8px}.site-header .site-mobile-group .site-menu-card{min-height:0;padding:8px 26px 8px 8px;font-size:12.5px}.site-header .site-mobile-group .site-menu-card b{right:8px}.site-header .site-mobile-all{padding:8px;color:var(--red);font-size:11.5px;font-weight:700;text-decoration:none}
    }
    @media(max-width:560px){:root{--site-header-height:58px}.site-header .site-header-in{gap:8px}.site-header .site-brand-logo{width:98px}.site-header .site-theme-toggle,.site-header .site-mobile-menu>summary{width:34px;height:34px}.site-header .site-theme-toggle svg{width:16px;height:16px}.site-header .site-mobile-popover{top:42px;right:-4px}}
  `;
  document.head.appendChild(style);
})();
