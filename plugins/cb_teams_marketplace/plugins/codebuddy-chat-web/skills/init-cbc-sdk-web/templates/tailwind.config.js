/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'var(--td-bg-color-page)',
        foreground: 'var(--td-text-color-primary)',
        muted: {
          DEFAULT: 'var(--td-bg-color-component)',
          foreground: 'var(--td-text-color-secondary)',
        },
        border: 'var(--td-component-stroke)',
        input: 'var(--td-bg-color-component)',
        card: {
          DEFAULT: 'var(--td-bg-color-container)',
          foreground: 'var(--td-text-color-primary)',
        },
        accent: {
          DEFAULT: 'var(--td-brand-color)',
          foreground: 'var(--td-text-color-anti)',
          light: 'var(--td-brand-color-light)',
        },
        primary: {
          DEFAULT: 'var(--td-text-color-primary)',
          foreground: 'var(--td-bg-color-page)',
        }
      },
      borderRadius: {
        'xl': '16px',
        '2xl': '20px',
      },
      animation: {
        'cursor-blink': 'blink 1s infinite',
      },
      keyframes: {
        blink: {
          '0%, 50%': { opacity: '1' },
          '51%, 100%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: false,
  }
}
