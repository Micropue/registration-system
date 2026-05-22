import { fileURLToPath, URL } from 'node:url'
import Vue from '@vitejs/plugin-vue'
import Fonts from 'unplugin-fonts/vite'
import { defineConfig } from 'vite'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import viteCompression from 'vite-plugin-compression'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    Vue({
      template: { transformAssetUrls },
    }),
    Vuetify({
      autoImport: true,
      styles: {
        configFile: 'src/styles/settings.scss',
      },
    }),
    Fonts({
      fontsource: {
        families: [
          {
            name: 'Roboto',
            weights: [100, 300, 400, 500, 700, 900],
            styles: ['normal', 'italic'],
          },
        ],
      },
    }),
    viteCompression({ algorithm: 'gzip', ext: '.gz', threshold: 0, filter: /\.(js|mjs|css|html|json|svg|xml|txt|ico)$/i }),
    VitePWA({
      registerType: 'prompt',
      manifest: {
        name: '哆啦A梦（校园跑版）',
        short_name: '校园跑登记',
        description: '虎虎校园跑登记系统',
        theme_color: '#1867C0',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          { src: '/pwa-48x48.png',   sizes: '48x48',   type: 'image/png' },
          { src: '/pwa-72x72.png',   sizes: '72x72',   type: 'image/png' },
          { src: '/pwa-96x96.png',   sizes: '96x96',   type: 'image/png' },
          { src: '/pwa-128x128.png', sizes: '128x128', type: 'image/png' },
          { src: '/pwa-144x144.png', sizes: '144x144', type: 'image/png' },
          { src: '/pwa-152x152.png', sizes: '152x152', type: 'image/png' },
          { src: '/pwa-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
          { src: '/pwa-384x384.png', sizes: '384x384', type: 'image/png' },
          { src: '/pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
      },
    }),
  ],
  define: { 'process.env': {} },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('src', import.meta.url)),
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.ts',
      '.tsx',
      '.vue',
    ],
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target:"http://localhost:8001/",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, '')
      },
      '/media': {
        target: 'http://localhost:8001/',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true,
        changeOrigin: true
      }
    }
  },
})
