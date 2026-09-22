/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#090d16",
        surface: "#111827",
        "surface-raised": "#1e293b",
        "surface-border": "#334155",
        brand: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
        },
        accent: {
          400: "#38bdf8",
          500: "#0ea5e9",
        }
      },
    },
  },
  plugins: [],
};
