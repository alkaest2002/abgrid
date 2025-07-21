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
                group: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.group.html'),
                dropzone: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.dropzone.html'),
                notifyReport: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.notify.report.html'),
                notifyErrorYaml: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.notify.error.yaml.html'),
                notifyErrorApi: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.notify.error.api.html'),
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