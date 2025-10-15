function showPopup(message, type) {
  let popup = document.createElement('div');
  popup.className = 'dashboard-popup ' + (type||'info');
  popup.textContent = message;
  document.body.appendChild(popup);
  setTimeout(() => { popup.classList.add('show'); }, 10);
  setTimeout(() => { popup.classList.remove('show'); setTimeout(()=>popup.remove(),400); }, 3000);
}

function showSuccessPopup(message, type) {
  // Create the main popup
  let popup = document.createElement('div');
  popup.className = 'dashboard-popup success-celebration ' + (type||'success');
  popup.innerHTML = `
    <div class="celebration-content">
      <div class="celebration-emoji">🎉</div>
      <div class="celebration-text">${message}</div>
    </div>
  `;
  document.body.appendChild(popup);
  
  // Only add celebration particles for connection establishments
  if (message.includes('Connection established') || message.includes('connected with')) {
    createCelebrationParticles();
  }
  
  // Show popup with animation
  setTimeout(() => { popup.classList.add('show'); }, 10);
  
  // Hide popup after delay
  setTimeout(() => { 
    popup.classList.remove('show'); 
    setTimeout(()=>popup.remove(),400); 
  }, 4000);
}


function showWelcomePopup(message, type) {
  // Create a welcome popup with special styling
  let popup = document.createElement('div');
  popup.className = 'dashboard-popup welcome-popup ' + (type||'success');
  popup.innerHTML = `
    <div class="welcome-content">
      <div class="welcome-emoji">👋</div>
      <div class="welcome-text">${message}</div>
    </div>
  `;
  document.body.appendChild(popup);
  
  // Show popup with animation
  setTimeout(() => { popup.classList.add('show'); }, 10);
  
  // Hide popup after delay
  setTimeout(() => { 
    popup.classList.remove('show'); 
    setTimeout(()=>popup.remove(),400); 
  }, 4000);
}

function createCelebrationParticles() {
  const particleCount = 20;
  const colors = ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'];
  const emojis = ['🎉', '✨', '🌟', '💫', '🎊', '🚀'];
  
  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.className = 'celebration-particle';
    particle.textContent = emojis[Math.floor(Math.random() * emojis.length)];
    particle.style.position = 'fixed';
    particle.style.left = '50%';
    particle.style.top = '50%';
    particle.style.fontSize = '20px';
    particle.style.pointerEvents = 'none';
    particle.style.zIndex = '10000';
    particle.style.animation = `particleExplosion ${2 + Math.random() * 2}s ease-out forwards`;
    particle.style.animationDelay = `${Math.random() * 0.5}s`;
    
    // Random direction
    const angle = (Math.PI * 2 * i) / particleCount;
    const velocity = 100 + Math.random() * 100;
    const x = Math.cos(angle) * velocity;
    const y = Math.sin(angle) * velocity;
    
    particle.style.setProperty('--x', x + 'px');
    particle.style.setProperty('--y', y + 'px');
    
    document.body.appendChild(particle);
    
    // Remove particle after animation
    setTimeout(() => {
      if (particle.parentNode) {
        particle.parentNode.removeChild(particle);
      }
    }, 3000);
  }
}