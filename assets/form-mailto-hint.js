(()=>{
  const form=document.getElementById('demo-form');
  if(!form)return;
  if(document.title.includes('Аттестация комплекса')){
    document.body.classList.add('attestation-page');
    const policy=form.querySelector('.policy');
    if(policy)policy.remove();
  }
  const button=form.querySelector('[type="submit"]');
  if(!button)return;
  button.textContent='Подготовить письмо';
  if(form.querySelector('.form-mailto-hint'))return;
  const hint=document.createElement('p');
  hint.className='form-mailto-hint';
  hint.textContent='Откроется почтовое приложение с подготовленным письмом. Для отправки нажмите «Отправить» в нём.';
  button.insertAdjacentElement('afterend',hint);
})();
