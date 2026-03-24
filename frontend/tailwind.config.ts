import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        upstream: {
          50: '#f0f9f4',
          100: '#dcf0e4',
          200: '#bbe1cc',
          300: '#8bcaab',
          400: '#57ad84',
          500: '#359167',
          600: '#267352',
          700: '#1f5c43',
          800: '#1b4a37',
          900: '#173d2e',
          950: '#0b221a',
        },
        accent: {
          50: '#fff8ed',
          100: '#ffefd4',
          200: '#ffdba8',
          300: '#ffc071',
          400: '#ff9d38',
          500: '#ff7e12',
          600: '#f06008',
          700: '#c74509',
          800: '#9e3710',
          900: '#7f2f10',
          950: '#451506',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Montserrat', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
