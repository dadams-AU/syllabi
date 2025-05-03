// Theme toggle functionality
function toggleTheme() {
    const html = document.documentElement;
    html.classList.toggle('dark');
  
    // Save preference
    if (html.classList.contains('dark')) {
      localStorage.setItem('theme', 'dark');
      updateThemeIcon('moon');
    } else {
      localStorage.setItem('theme', 'light');
      updateThemeIcon('sun');
    }
  }
  
  function updateThemeIcon(theme) {
    const sunIcon = document.getElementById('sunIcon');
    const moonIcon = document.getElementById('moonIcon');
    if (theme === 'sun') {
      sunIcon.classList.remove('hidden');
      moonIcon.classList.add('hidden');
    } else {
      sunIcon.classList.add('hidden');
      moonIcon.classList.remove('hidden');
    }
  }
  
  function initTheme() {
    const saved = localStorage.getItem('theme');
    const html = document.documentElement;
    if (
      saved === 'dark' ||
      (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)
    ) {
      html.classList.add('dark');
      updateThemeIcon('moon');
    } else {
      html.classList.remove('dark');
      updateThemeIcon('sun');
    }
  }
  
  document.addEventListener('DOMContentLoaded', initTheme);