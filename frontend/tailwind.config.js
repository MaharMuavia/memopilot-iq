/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef6ff",
          100: "#d9ebff",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
      },
      boxShadow: {
        glass: "0 8px 32px rgba(31, 41, 55, 0.08)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
