import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path' // 💡 引入 path 模組

export default defineConfig({
  base: './',
  plugins: [vue()],
  resolve: {
    alias: {
      // 💡 設定 @ 別名指向 src 資料夾
      '@': path.resolve(__dirname, './src'),
    },
  },
})
