import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import { defineConfig } from 'vite'

const root = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig({
  plugins: [{
    name: 'slidev-virtual-slide-assets',
    resolveId(source, importer) {
      if (source.startsWith('.') && importer?.includes('__slidev_')) return resolve(root, source)
    },
  }],
  server: { fs: { strict: false } },
})
