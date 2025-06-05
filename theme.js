// theme.js

// When the page loads, read localStorage and show the correct icon.
document.addEventListener('DOMContentLoaded', () => {
  const html = document.documentElement;
  const sunIcon  = document.getElementById('sunIcon');
  const moonIcon = document.getElementById('moonIcon');
  const savedTheme = localStorage.getItem('theme');

  if (savedTheme === 'dark') {
    html.classList.add('dark');
    sunIcon.classList.remove('hidden');
    moonIcon.classList.add('hidden');
  } else {
    html.classList.remove('dark');
    sunIcon.classList.add('hidden');
    moonIcon.classList.remove('hidden');
  }
});

// Define toggleTheme so that the button can call it.
function toggleTheme() {
  const html     = document.documentElement;
  const sunIcon  = document.getElementById('sunIcon');
  const moonIcon = document.getElementById('moonIcon');
  const isDark   = html.classList.toggle('dark');

  localStorage.setItem('theme', isDark ? 'dark' : 'light');

  if (isDark) {
    sunIcon.classList.remove('hidden');
    moonIcon.classList.add('hidden');
  } else {
    sunIcon.classList.add('hidden');
    moonIcon.classList.remove('hidden');
  }
}
