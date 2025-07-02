import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [
    tailwindcss(),
    basicSsl({
      /** name of certification */
      name: 'abgrid',
      /** custom trust domains */
      domains: ['*.auth0.com'],
      /** custom certification directory */
      certDir: '.devServer/cert'
    })
  ],
})