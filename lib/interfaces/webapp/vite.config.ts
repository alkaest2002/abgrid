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
                itGroup: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.group.html'),
                itDropzoneEmpty: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.dropzone.empty.html'),
                itDropzoneData: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.dropzone.data.html'),
                itNotifyReport: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.notify.report.html'),
                itNotifyErrorYaml: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.notify.error.yaml.html'),
                itNotifyErrorApi: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.notify.error.api.html'),
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