(()=>{
  const header=document.querySelector('.header');
  if(!header)return;

  const source=decodeURIComponent(location.pathname).includes('/макеты/');
  const productsPath=source?'02_Готовый_вариант_Интеграция_Фантом_и_1С_CRM.html':'/';
  const solutionsPath=source?'03_Готовый_вариант_Электроэнергетика.html':'electroenergetika.html';
  const items=[
    {label:'Решения',href:solutionsPath},
    {label:'Продукты',href:productsPath},
    {label:'Услуги',href:'https://mdis.ru/service/'},
    {label:'Новости',href:'https://mdis.ru/news/'},
    {label:'Поддержка',href:'https://mdis.ru/support/'},
    {label:'Компания',href:'https://mdis.ru/about/'}
  ];
  const links=items.map(item=>`<a href="${item.href}">${item.label}</a>`).join('');

  header.className='header site-header';
  header.innerHTML=`<div class="wrap header-in site-header-in"><a class="brand site-brand" href="${productsPath}" aria-label="Phantom — главная"><img class="site-brand-logo" src="assets/logos/phantom-black.svg" alt="Phantom"></a><nav class="nav site-nav" aria-label="Основная навигация">${links}</nav><details class="mobile-menu site-mobile-menu"><summary aria-label="Открыть меню"></summary><nav class="site-mobile-popover" aria-label="Основная навигация">${links}</nav></details></div>`;

  const mobileMenu=header.querySelector('.site-mobile-menu');
  document.addEventListener('click',event=>{
    if(mobileMenu&&!mobileMenu.contains(event.target))mobileMenu.removeAttribute('open');
  });

  if(document.getElementById('site-header-style'))return;
  const style=document.createElement('style');
  style.id='site-header-style';
  style.textContent=`
    .site-header{position:sticky;top:0;z-index:30;border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--paper) 94%,transparent);backdrop-filter:blur(16px)}
    .site-header .site-header-in{min-height:76px;gap:clamp(18px,2.5vw,34px)}
    .site-header .site-brand{display:flex;flex:0 0 auto;align-items:center;margin-right:auto;text-decoration:none}
    .site-header .site-brand-logo{display:block;width:120px;height:auto}
    .site-header .site-nav{display:flex;align-items:center;gap:clamp(16px,2vw,28px);margin-left:0;color:var(--muted);font-size:13px;font-weight:800}
    .site-header .site-nav a{position:relative;padding:28px 0 25px;color:inherit;text-decoration:none;white-space:nowrap;transition:color .18s}
    .site-header .site-nav a:after{position:absolute;right:0;bottom:19px;left:0;height:2px;background:var(--red);content:"";opacity:0;transform:scaleX(.35);transition:opacity .18s,transform .18s}
    .site-header .site-nav a:hover,.site-header .site-nav a:focus-visible{color:var(--ink);outline:none}
    .site-header .site-nav a:hover:after,.site-header .site-nav a:focus-visible:after{opacity:1;transform:scaleX(1)}
    .site-header .site-mobile-menu{display:none!important}
    html[data-theme="dark"] .site-header .site-brand-logo{filter:invert(1) brightness(2)}
    @media(max-width:1080px){
      .site-header .site-nav{display:none!important}
      .site-header .site-mobile-menu{position:relative;display:block!important;margin-left:auto}
      .site-header .site-mobile-menu summary{display:grid;place-items:center;width:42px;height:42px;list-style:none;border:1px solid var(--line);border-radius:50%;color:var(--ink);cursor:pointer}
      .site-header .site-mobile-menu summary::-webkit-details-marker{display:none}
      .site-header .site-mobile-menu summary:before{content:"☰";font-size:20px;line-height:1}
      .site-header .site-mobile-menu[open] summary:before{content:"×";font-size:25px;font-weight:400}
      .site-header .site-mobile-popover{position:absolute;top:53px;right:0;display:grid;min-width:220px;padding:8px;border:1px solid var(--line);border-radius:10px;background:var(--paper);box-shadow:0 18px 42px #12203624}
      .site-header .site-mobile-popover a{padding:10px 12px;border-radius:6px;color:var(--ink);font-size:13px;font-weight:800;text-decoration:none}
      .site-header .site-mobile-popover a:hover,.site-header .site-mobile-popover a:focus-visible{background:var(--soft);color:var(--red);outline:none}
    }
    @media(max-width:560px){.site-header .site-header-in{min-height:66px}.site-header .site-brand-logo{width:106px}}
  `;
  document.head.appendChild(style);
})();
