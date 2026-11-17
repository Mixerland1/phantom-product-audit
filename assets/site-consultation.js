/* Common engineer consultation — same copy/fields/action as phantom-home.html. */
(() => {
  'use strict';
  const install = () => {
    const main = document.querySelector('main');
    const footer = document.querySelector('footer.footer');
    if (!main || !footer || main.querySelector('.site-consultation')) return;

    // The homepage already contains the canonical form and should not get a duplicate.
    if (main.querySelector('.contact-area #contact-form')) return;

    const page = (location.pathname.split('/').pop() || '').toLowerCase();
    const supportPage = /^(support(?:-|\.html)|faq\.html|contacts\.html|privacy-policy\.html|cookie-policy\.html|requisites\.html|training\.html|partners\.html|migration-progress\.html)/.test(page);
    const sections = [...main.querySelectorAll('section')];
    const last = sections.at(-1);
    let oldAnchor = '';
    if (last && !supportPage) {
      const heading = (last.querySelector('h2')?.textContent || '').trim();
      const kind = `${last.id} ${last.className}`;
      const looksLikeRequest = /подбер|конфигураци|нужна|нужен|обсудить|свяжитесь|подключение|заявк/i.test(heading)
        || /(?:^|[\s_-])(?:request|contact|consultation|callback|inquiry)(?:$|[\s_-])/i.test(kind);
      const hasSalesAction = !!last.querySelector('a[href^="mailto:sales@mdis.ru"], form');
      if (looksLikeRequest && hasSalesAction) {
        // Preserve any deep links to the former request section and leave its
        // markup intact for existing page scripts, while showing one unified CTA.
        oldAnchor = last.id && last.id !== 'site-consultation' ? last.id : '';
        if (oldAnchor) last.removeAttribute('id');
        last.hidden = true;
        last.inert = true;
        last.setAttribute('aria-hidden', 'true');
        last.style.setProperty('display', 'none', 'important');
      }
    }

    const section = document.createElement('section');
    section.className = 'site-consultation';
    section.id = 'site-consultation';
    section.setAttribute('aria-labelledby', 'site-consultation-heading');
    section.innerHTML = `
      ${oldAnchor ? `<span class="sc-anchor" id="${oldAnchor}"></span>` : ''}
      <div class="sc-wrap"><div class="sc-panel">
        <div>
          <p class="sc-eyebrow">Консультация инженера</p>
          <h2 id="site-consultation-heading">Подберём конфигурацию под&nbsp;вашу задачу</h2>
          <p class="sc-text">Укажите типы подключаемых линий, приблизительное количество каналов и&nbsp;требования к&nbsp;записи. Специалисты МДИС помогут определить возможный состав системы.</p>
          <div class="sc-links"><a href="tel:+74957833379">+7 (495) 783-33-79</a><a href="mailto:sales@mdis.ru">sales@mdis.ru</a></div>
        </div>
        <form class="sc-form" id="site-consultation-form">
          <label class="sc-field">Компания<input type="text" name="company" autocomplete="organization" placeholder="Название организации"></label>
          <label class="sc-field">Ваше имя<input type="text" name="name" autocomplete="name" placeholder="Как к вам обращаться"></label>
          <label class="sc-field sc-field-wide">Email для&nbsp;связи<input type="email" name="email" autocomplete="email" required placeholder="name@company.ru"></label>
          <label class="sc-field sc-field-wide">Задача<textarea name="task" required placeholder="Например: 64 канала, резервирование, доступ к архиву"></textarea></label>
          <button type="submit">Подготовить письмо инженеру</button>
          <p class="sc-note">Форма не&nbsp;передаёт данные на&nbsp;сервер. Кнопка откроет почтовую программу с&nbsp;подготовленным письмом. Для&nbsp;отправки потребуется подтвердить отправку в&nbsp;почтовом приложении.</p>
        </form>
      </div></div>`;
    main.append(section);
    const form = section.querySelector('#site-consultation-form');
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const lines = ['Здравствуйте!', '',
        'Компания: ' + String(data.get('company') || '').trim(),
        'Имя: ' + String(data.get('name') || '').trim(),
        'Email: ' + String(data.get('email') || '').trim(), '',
        'Задача:', String(data.get('task') || '').trim()];
      window.location.href = 'mailto:sales@mdis.ru?subject=' +
        encodeURIComponent('Запрос с сайта Phantom') + '&body=' + encodeURIComponent(lines.join('\n'));
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, {once:true});
  else install();
})();