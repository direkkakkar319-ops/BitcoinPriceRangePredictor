/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B0D10',
        panel: '#13171C',
        line: '#1F242B',
        ink: '#E7ECEF',
        mute: '#8A95A1',
        btc: '#F7931A',
        up: '#22C55E',
        down: '#EF4444',
        band: '#60A5FA',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
