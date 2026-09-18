import { resolve } from 'node:path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [{
    name: 'slidev-virtual-slide-assets',
    resolveId(source, importer) {
      if (importer?.includes('__slidev_') && /^\.\/(images|videos)\//.test(source)) return resolve(process.cwd(), source)
    },
  }],
  server: { fs: { strict: false } },
})
