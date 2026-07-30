/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // رنگ‌های اختصاصی تم بنفش تیره و یاسی
        dark: {
          bg: '#0f0c1b',
          card: '#18132a',
          border: '#2a2243',
        },
        lilac: {
          light: '#e9d5ff',
          DEFAULT: '#c084fc',
          dark: '#a855f7',
        }
      }
    },
  },
  plugins: [],
}
