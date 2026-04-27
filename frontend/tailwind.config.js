/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#1A3ED4',
          light: '#E8EDFB',
          hover: '#1430B0',
        },
        success: '#1E8C45',
        error: '#D93025',
        warning: '#F5820D',
      },
      fontFamily: {
        sans: ['Inter', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
