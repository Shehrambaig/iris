/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tradingview-bg': '#000000',
        'tradingview-panel': '#1E222D',
        'tradingview-border': '#2A2E39',
        'tradingview-text': '#D1D4DC',
        'tradingview-green': '#26A69A',
        'tradingview-red': '#EF5350',
      },
    },
  },
  plugins: [],
}
