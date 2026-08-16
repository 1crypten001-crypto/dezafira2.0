/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff4ec",
          100: "#ffe6d3",
          200: "#ffcba6",
          300: "#ffa86e",
          400: "#ff7a2a",
          500: "#f85808",
          600: "#e04a00",
          700: "#b83c04",
          800: "#93300a",
          900: "#78290b",
        },
      },
    },
  },
  plugins: [],
};
