function showPopup(message, type) {
  let popup = document.createElement('div');
  popup.className = 'dashboard-popup ' + (type||'info');
  popup.textContent = message;
  document.body.appendChild(popup);
  setTimeout(() => { popup.classList.add('show'); }, 10);
  setTimeout(() => { popup.classList.remove('show'); setTimeout(()=>popup.remove(),400); }, 3000);
}
