/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./js/**/*.js", // To scan JS files if we add dynamic classes
  ],
  darkMode: 'class', // or 'media' if you prefer OS-level settings
  theme: {
    extend: {
      colors: {
        'base-light': '#F8F8F2',
        'text-light': '#1C1C1C',
        'accent1-light': '#39FF14', // Neon Green
        'accent2-light': '#FF00FF', // Neon Pink

        'base-dark': '#0B0B0B',
        'text-dark': '#D3D3D3',   // Silver-Gray
        'accent1-dark': '#00FFD7', // Teal
        'accent2-dark': '#FF1CED', // Magenta

        // For semantic naming if preferred directly in Tailwind (won't dynamically change with theme switcher)
        // These are static and won't be affected by the JS theme switcher's data-theme attribute.
        // The dynamic theming will primarily rely on CSS variables defined in styles.css.
      },
      fontFamily: {
        primary: ['Roboto', 'Poppins', 'sans-serif'], // Modern sans-serif
        secondary: ['"Press Start 2P"', '"VT323"', 'cursive'], // Pixelated/block style
      },
      borderRadius: {
        'card': '0.5rem',
      },
      gap: {
        'grid': '1rem',
      }
    },
  },
  plugins: [],
}
