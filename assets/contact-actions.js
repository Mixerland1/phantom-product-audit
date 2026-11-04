(() => {
  const request = document.querySelector('.request');
  if (!request || request.querySelector('.contact-actions')) return;

  let layout = request.querySelector('.request-in');
  if (!layout) {
    layout = document.createElement('div');
    layout.className = 'request-in';
    while (request.firstChild) layout.appendChild(request.firstChild);
    request.appendChild(layout);
  }

  const contacts = layout.querySelector('.contacts');
  if (contacts) contacts.remove();

  const actions = document.createElement('div');
  actions.className = 'contact-actions';
  actions.setAttribute('aria-label', 'Связаться с МДИС');
  actions.innerHTML = `
    <a class="contact-action" href="tel:+74957833379">
      <span class="contact-action-title">Позвоните</span>
      <span class="contact-action-copy">Чтобы обсудить задачу и получить консультацию</span>
      <strong>+7 (495) 783-33-79</strong>
    </a>
    <a class="contact-action" href="mailto:sales@mdis.ru">
      <span class="contact-action-title">Напишите</span>
      <span class="contact-action-copy">Чтобы описать задачу и получить консультацию</span>
      <strong>sales@mdis.ru</strong>
    </a>`;
  layout.prepend(actions);
})();
