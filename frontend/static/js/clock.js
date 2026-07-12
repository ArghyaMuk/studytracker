function updateClock() {
    const now = new Date();
    const time = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
    const date = now.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
    const el = document.getElementById('clock');
    if (el) el.textContent = time + '  |  ' + date;
}
updateClock();
setInterval(updateClock, 1000);
