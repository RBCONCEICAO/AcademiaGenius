/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4F46E5', // Indigo-700
        secondary: '#4B5563', // Gray-700
        accent: '#14B8A6', // Teal-500
        success: '#22C55E', // Green-500
        warning: '#F97316', // Orange-500
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
