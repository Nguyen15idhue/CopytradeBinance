/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        app: "var(--bg)",
        panel: "var(--panel)",
        elevated: "var(--elevated)",
        line: "var(--line)",
        strong: "var(--text-strong)",
        body: "var(--text-body)",
        muted: "var(--text-muted)",
        faint: "var(--text-faint)",
        accent: "var(--accent)",
        info: "var(--info)",
        warn: "var(--warn)",
        danger: "var(--danger)",
      },
    },
  },
  plugins: [],
};
