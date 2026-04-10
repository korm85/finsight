/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B0E11',
        surface: '#13171C',
        'surface-elevated': '#1C2127',
        border: '#2A2F38',
        'text-primary': '#E8EAED',
        'text-secondary': '#8B9199',
        'accent-green': '#00C853',
        'accent-red': '#FF1744',
        'accent-blue': '#2979FF',
        'accent-gold': '#FFD600',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
