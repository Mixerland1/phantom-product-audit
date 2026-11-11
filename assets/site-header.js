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
    {label:'Атомная энергетика',href:'https://mdis.ru/solution/atom_icon/'},
    {label:'Коммерческие предприятия',href:'https://mdis.ru/solution/commercical/'},
    {label:'Промышленные предприятия',href:'https://mdis.ru/solution/prom/'},
    {label:'Автосалоны',href:'https://mdis.ru/solution/auto/'},
    {label:'Госструктуры',href:'https://mdis.ru/solution/gos/'},
    {label:'Финансовые организации',href:'https://mdis.ru/solution/financical/'},
    {label:'Электроэнергетика',href:paths.electro},
    {label:'Авиация и\u00a0транспорт',href:paths.aviation},
    {label:'Персональные решения',href:'https://mdis.ru/service/personalnye-resheniya/'}
  ];
  const products=[
    {label:'Запись телефонных переговоров',href:'https://mdis.ru/catalog/'},
    {label:'Запись диспетчерских переговоров',href:'https://mdis.ru/catalog/'},
    {label:'Запись IP-телефонии',href:'https://mdis.ru/catalog/zapis-ip-telefonii/'},
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
  const desktopNav=`${desktopMenu('Решения',solutions,paths.home+'#industries','О\u00a0решениях Phantom')}${desktopMenu('Продукты',products,paths.home+'#products','О\u00a0продуктах Phantom')}${direct}`;
  const mobileNav=`${mobileMenu('Решения',solutions,paths.home+'#industries','О\u00a0решениях Phantom')}${mobileMenu('Продукты',products,paths.home+'#products','О\u00a0продуктах Phantom')}${direct}`;

  header.className='header site-header';
  header.innerHTML=`<div class="wrap header-in site-header-in"><a class="brand site-brand" href="${paths.home}" aria-label="Phantom — главная"><img class="site-brand-logo" src="assets/logos/phantom-black.svg" alt="Phantom"></a><nav class="nav site-nav" aria-label="Основная навигация">${desktopNav}</nav><button class="site-theme-toggle" id="theme-toggle" type="button" aria-label="Переключить цветовую тему"></button><details class="mobile-menu site-mobile-menu"><summary aria-label="Открыть меню"></summary><nav class="site-mobile-popover" aria-label="Основная навигация">${mobileNav}</nav></details></div>`;

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
    .site-header{position:sticky;top:0;z-index:30;border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--paper) 94%,transparent);backdrop-filter:blur(16px)}
    .site-header .site-header-in{display:flex;align-items:center;min-height:76px;gap:clamp(14px,1.75vw,25px)}
    .site-header .site-brand{display:flex;flex:0 0 auto;align-items:center;margin-right:auto;text-decoration:none}
    .site-header .site-brand-logo{display:block;width:120px;height:auto}
    .site-header .site-nav{display:flex;align-items:stretch;gap:clamp(15px,1.6vw,24px);margin-left:0;color:var(--muted);font-size:13px;font-weight:800}
    .site-header .site-nav>a,.site-header .site-menu>summary{position:relative;display:flex;align-items:center;gap:6px;height:76px;padding:0;color:inherit;font:inherit;text-decoration:none;white-space:nowrap;cursor:pointer;list-style:none}
    .site-header .site-menu>summary::-webkit-details-marker{display:none}
    .site-header .site-menu>summary i{width:7px;height:7px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:translateY(-2px) rotate(45deg);transition:transform .18s}
    .site-header .site-menu[open]>summary i{transform:translateY(2px) rotate(225deg)}
    .site-header .site-nav>a:after,.site-header .site-menu>summary:after{position:absolute;right:0;bottom:19px;left:0;height:2px;background:var(--red);content:"";opacity:0;transform:scaleX(.35);transition:opacity .18s,transform .18s}
    .site-header .site-nav>a:hover,.site-header .site-nav>a:focus-visible,.site-header .site-menu>summary:hover,.site-header .site-menu>summary:focus-visible,.site-header .site-menu[open]>summary{color:var(--ink);outline:none}
    .site-header .site-nav>a:hover:after,.site-header .site-nav>a:focus-visible:after,.site-header .site-menu>summary:hover:after,.site-header .site-menu>summary:focus-visible:after,.site-header .site-menu[open]>summary:after{opacity:1;transform:scaleX(1)}
    .site-header .site-menu{position:relative}
    .site-header .site-menu-panel{position:absolute;top:66px;left:-20px;width:410px;padding:14px 20px 20px;border:1px solid var(--line);border-radius:14px;background:var(--paper);box-shadow:0 22px 54px #1220362b}
    .site-header .site-menu-list{display:grid;grid-template-columns:1fr 1fr;gap:6px}
    .site-header .site-menu-card{position:relative;display:flex;align-items:center;min-height:54px;padding:10px 30px 10px 12px;border:1px solid transparent;border-radius:9px;color:var(--ink);font-size:13px;font-weight:850;line-height:1.2;text-decoration:none;transition:border-color .18s,background .18s,color .18s}
    .site-header .site-menu-card b{position:absolute;right:11px;color:var(--red);font-size:14px}
    .site-header .site-menu-card:hover,.site-header .site-menu-card:focus-visible{border-color:var(--line);background:var(--soft);color:var(--red);outline:none}
    .site-header .site-menu-all{display:flex;align-items:center;justify-content:space-between;margin-top:12px;padding:12px 4px 0;border-top:1px solid var(--line);color:var(--ink);font-size:12px;font-weight:900;text-decoration:none}
    .site-header .site-menu-all b{color:var(--red);font-size:16px}.site-header .site-menu-all:hover,.site-header .site-menu-all:focus-visible{color:var(--red);outline:none}
    .site-header .site-theme-toggle{flex:0 0 auto;display:grid;place-items:center;width:42px;height:42px;padding:0;border:1px solid var(--line);border-radius:50%;background:transparent;color:var(--ink);cursor:pointer;transition:background .18s,border-color .18s,color .18s}
    .site-header .site-theme-toggle svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
    .site-header .site-theme-toggle:hover,.site-header .site-theme-toggle:focus-visible{border-color:var(--ink);background:var(--soft);outline:none}
    .site-header .site-mobile-menu{display:none!important}
    html[data-theme="dark"] .site-header .site-brand-logo{filter:invert(1) brightness(2)}
    @media(max-width:1080px){
      .site-header .site-nav{display:none!important}.site-header .site-mobile-menu{position:relative;display:block!important}.site-header .site-mobile-menu>summary{display:grid;place-items:center;width:42px;height:42px;list-style:none;border:1px solid var(--line);border-radius:50%;color:var(--ink);cursor:pointer}.site-header .site-mobile-menu>summary::-webkit-details-marker{display:none}.site-header .site-mobile-menu>summary:after{content:none!important}.site-header .site-mobile-menu>summary:before{content:"☰";font-size:20px;line-height:1}.site-header .site-mobile-menu[open]>summary:before{content:"×";font-size:25px;font-weight:400}
      .site-header .site-mobile-popover{position:absolute;top:53px;right:0;display:grid;min-width:min(340px,calc(100vw - 40px));padding:8px;border:1px solid var(--line);border-radius:10px;background:var(--paper);box-shadow:0 18px 42px #12203624}.site-header .site-mobile-popover>a{display:block;padding:11px 12px;border-radius:6px;color:var(--ink);font-size:13px;font-weight:800;text-decoration:none}.site-header .site-mobile-popover>a:hover,.site-header .site-mobile-popover>a:focus-visible{background:var(--soft);color:var(--red);outline:none}
      .site-header .site-mobile-group{border-bottom:1px solid var(--line)}.site-header .site-mobile-group:last-of-type{border-bottom:0}.site-header .site-mobile-group summary{display:flex;align-items:center;justify-content:space-between;padding:11px 12px;color:var(--ink);font-size:13px;font-weight:850;cursor:pointer;list-style:none}.site-header .site-mobile-group summary::-webkit-details-marker{display:none}.site-header .site-mobile-group summary:before,.site-header .site-mobile-group summary:after{content:none!important}.site-header .site-mobile-group summary i{width:7px;height:7px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:translateY(-2px) rotate(45deg)}.site-header .site-mobile-group[open] summary i{transform:translateY(2px) rotate(225deg)}
      .site-header .site-mobile-group>div{display:grid;gap:4px;padding:0 6px 9px}.site-header .site-mobile-group .site-menu-card{min-height:0;padding:9px 28px 9px 8px;font-size:12px}.site-header .site-mobile-group .site-menu-card b{right:9px}.site-header .site-mobile-all{padding:9px 8px;color:var(--red);font-size:12px;font-weight:900;text-decoration:none}
    }
    @media(max-width:560px){.site-header .site-header-in{min-height:66px;gap:9px}.site-header .site-brand-logo{width:106px}.site-header .site-theme-toggle{width:38px;height:38px}.site-header .site-theme-toggle svg{width:17px;height:17px}.site-header .site-mobile-popover{right:-5px}}
  `;
  document.head.appendChild(style);
})();
