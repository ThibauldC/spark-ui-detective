import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

const slides = fileURLToPath(new URL('./slides.md', import.meta.url))

export default defineConfig({
  resolve: {
    alias: [{ find: /^\/slides\.md(?=__slidev_)/, replacement: slides }],
  },
})
