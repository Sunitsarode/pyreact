import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Read settings.json
const settingsPath = path.resolve(__dirname, '../settings.json')
const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'))

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: settings.frontend_server?.port || 3000,
    strictPort: true
  }
})
