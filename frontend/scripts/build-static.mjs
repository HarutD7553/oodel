import { mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const repositoryRoot = resolve(frontendDir, '..')
const outputDir = resolve(frontendDir, 'dist')
const pages = ['index.html', 'baker.html', '404.html']

async function readLocalApiUrl() {
  try {
    const envFile = await readFile(resolve(frontendDir, '.env'), 'utf8')
    const line = envFile.split(/\r?\n/).find((entry) => entry.startsWith('VITE_API_URL='))
    return line?.slice('VITE_API_URL='.length).trim().replace(/^['"]|['"]$/g, '') || ''
  } catch {
    return ''
  }
}

const apiUrl = process.env.VITE_API_URL
  || await readLocalApiUrl()
  || (process.env.VITE_API_HOST ? `https://${process.env.VITE_API_HOST}` : 'http://127.0.0.1:8000')

await rm(outputDir, { recursive: true, force: true })
await mkdir(outputDir, { recursive: true })

for (const page of pages) {
  const source = await readFile(resolve(repositoryRoot, page), 'utf8')
  await writeFile(
    resolve(outputDir, page),
    source.replaceAll('__OODEL_API_URL__', apiUrl),
  )
}

console.log(`Built ${pages.length} Oodel pages in ${outputDir} (API: ${apiUrl})`)
