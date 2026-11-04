(()=>{
  const brand=document.querySelector('.header .brand');
  if(brand){
    brand.setAttribute('aria-label','Фантом');
    brand.innerHTML='<img class="brand-logo-light" src="assets/logos/phantom-black.svg" alt="Фантом"><img class="brand-logo-dark" src="assets/logos/phantom.svg" alt="">';
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
