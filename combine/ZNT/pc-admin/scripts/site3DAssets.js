import { createReadStream, copyFileSync, mkdirSync, readdirSync, existsSync, statSync } from 'node:fs'
import { resolve, sep, extname } from 'node:path'
import { fileURLToPath } from 'node:url'

// The project's 3D folder is the single source for the model and viewer UI.
const source = resolve(fileURLToPath(new URL('../../../../3D/', import.meta.url)))
const types = { '.html': 'text/html; charset=utf-8', '.glb': 'model/gltf-binary', '.png': 'image/png', '.txt': 'text/plain; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' }

function copyAssets(from, to) {
  mkdirSync(to, { recursive: true })
  for (const entry of readdirSync(from, { withFileTypes: true })) {
    const input = resolve(from, entry.name), output = resolve(to, entry.name)
    if (entry.isDirectory()) copyAssets(input, output)
    else if (entry.isFile()) copyFileSync(input, output)
  }
}

export default function site3DAssets() {
  let output, base
  return {
    name: 'sitesafe-3d-assets',
    configResolved(config) {
      output = resolve(config.root, config.build.outDir, '3D')
      base = config.base
    },
    configureServer(server) {
      server.middlewares.use(`${base}3D/`, (req, res, next) => {
        if (!['GET', 'HEAD'].includes(req.method)) { next(); return }
        let file
        try { file = resolve(source, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname)) }
        catch { res.statusCode = 400; res.end('Invalid asset path'); return }
        if (!file.startsWith(source + sep)) { res.statusCode = 403; res.end(); return }
        if (!existsSync(file) || !statSync(file).isFile()) { res.statusCode = 404; res.end('3D asset not found'); return }
        res.setHeader('Content-Type', types[extname(file).toLowerCase()] || 'application/octet-stream')
        res.setHeader('Content-Length', statSync(file).size)
        res.setHeader('Cache-Control', 'no-cache')
        if (req.method === 'HEAD') { res.end(); return }
        const stream = createReadStream(file)
        stream.on('error', () => res.destroy())
        stream.pipe(res)
      })
    },
    closeBundle() {
      if (!existsSync(source)) throw new Error(`3D asset folder is missing: ${source}`)
      copyAssets(source, output)
    },
  }
}
