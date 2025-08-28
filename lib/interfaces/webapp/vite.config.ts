// @ts-ignore
import { resolve } from "path";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
// @ts-ignore
import { fileURLToPath, URL } from "node:url"


export default defineConfig({
    envDir: '../../../', 
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
                itNotifyQueue: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.notify.queue.html'),
                itMultistepSociogram: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.multistep.sociogram.html'),
                itMultistepData: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.multistep.data.html'),
                itMultistepReport: resolve(fileURLToPath(new URL('.', import.meta.url)), 'pages/it.multistep.report.html'),
            }
        }
    },
    plugins: [
        tailwindcss()
    ],
})