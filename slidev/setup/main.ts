import { defineAppSetup } from '@slidev/types'

// Set VITE_NO_BG=1 to render slides without the EMFCC background images (smaller PDF exports).
export default defineAppSetup(() => {
  if (import.meta.env.VITE_NO_BG) document.documentElement.classList.add('no-bg')
})
