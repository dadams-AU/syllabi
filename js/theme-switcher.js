(function() {
    const themeToggleButton = document.getElementById('themeToggle');
    const iconSun = document.getElementById('icon-sun');
    const iconMoon = document.getElementById('icon-moon');
    const htmlElement = document.documentElement;

    // Function to apply the saved theme or default to light
    function applyTheme() {
        const savedTheme = localStorage.getItem('theme');
        // Default to 'light' if no theme is saved or if 'light' is explicitly set
        if (savedTheme === 'dark') {
            htmlElement.classList.add('dark');
            htmlElement.setAttribute('data-theme', 'dark');
            if (iconSun) iconSun.classList.remove('hidden');
            if (iconMoon) iconMoon.classList.add('hidden');
        } else {
            htmlElement.classList.remove('dark');
            htmlElement.setAttribute('data-theme', 'light');
            if (iconSun) iconSun.classList.add('hidden');
            if (iconMoon) iconMoon.classList.remove('hidden');
        }
    }

    // Function to toggle theme
    function toggleTheme() {
        if (htmlElement.classList.contains('dark')) {
            htmlElement.classList.remove('dark');
            htmlElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            if (iconSun) iconSun.classList.add('hidden');
            if (iconMoon) iconMoon.classList.remove('hidden');
        } else {
            htmlElement.classList.add('dark');
            htmlElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            if (iconSun) iconSun.classList.remove('hidden');
            if (iconMoon) iconMoon.classList.add('hidden');
        }
    }

    // Event listener for the theme toggle button
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            toggleTheme();
        });
    }

    // Apply theme on initial load
    // The inline script in <head> handles the very first paint.
    // This function ensures consistency if the script is deferred or if state needs re-evaluation.
    // However, the primary mechanism for FOUC prevention is the head script.
    // We call it here to ensure icons are correctly set based on the theme determined by the head script.
    applyTheme();

    // Optional: Listen for storage changes from other tabs/windows
    window.addEventListener('storage', (event) => {
        if (event.key === 'theme') {
            applyTheme();
        }
    });

})();
