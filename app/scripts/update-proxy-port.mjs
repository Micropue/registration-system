import { readFileSync, writeFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const configPath = resolve(__dirname, '../vite.config.mts')

let content = readFileSync(configPath, 'utf-8')
const original = content

content = content.replace(/localhost:8001/g, 'localhost:8000')

if (content !== original) {
  writeFileSync(configPath, content, 'utf-8')
  console.log('✓ Proxy port updated from 8001 to 8000')
} else {
  console.log('✓ Proxy port already set to 8000 (no change needed)')
}
