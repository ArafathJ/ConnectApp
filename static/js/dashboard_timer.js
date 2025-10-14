function startTimer(seconds) {
  let timerDisplay = document.getElementById("timer");
  function update() {
    let h = Math.floor(seconds / 3600);
    let m = Math.floor((seconds % 3600) / 60);
    let s = seconds % 60;
    timerDisplay.textContent = `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
    if (seconds > 0) {
      seconds--; setTimeout(update, 1000);
    }
  }
  update();
}
