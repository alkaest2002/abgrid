// @ts-ignore
import { resolve } from "path";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import basicSsl from "@vitejs/plugin-basic-ssl";
// @ts-ignore
import { fileURLToPath, URL } from "node:url"


export default defineConfig({
    build: {
        rollupOptions: {
            input: {
                main: resolve(fileURLToPath(new URL('.', import.meta.url)), 'index.html'),
                about: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.dropzone.html'),
                contact: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.generate.html'),
                services: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.notify.html'),
            }
        }
    },
    plugins: [
        tailwindcss(),
        basicSsl({
            /** name of certification */
            name: "abgrid",
            /** custom trust domains */
            domains: [],
            /** custom certification directory */
            certDir: ".devServer/cert"
        }),
    ],
})