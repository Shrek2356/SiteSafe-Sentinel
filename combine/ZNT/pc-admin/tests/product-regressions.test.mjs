import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { containRect } from '../src/utils/videoGeometry.js'

test('portrait and landscape overlays stay on the contained image, not black bars', () => {
  assert.deepEqual(containRect(1000,600,1920,1080), { left:0, top:18.75, width:1000, height:562.5 })
  assert.deepEqual(containRect(1000,600,600,1200), { left:350, top:0, width:300, height:600 })
  assert.equal(containRect(0,600,1920,1080), null)
})

test('real login uses the entered account and password, not the role preset', async () => {
  const source = (await readFile(new URL('../src/api/auth.js', import.meta.url),'utf8'))
    .replace(/^import .*$/gm, '')
  const api = await import('data:text/javascript;base64,' + Buffer.from(
    'const USE_MOCK=false; const request={post:(url,data)=>({url,data})};\n'+source
  ).toString('base64'))
  assert.deepEqual(api.login({username:'new_manager',password:'custom-pass',role:'safety'}), {
    url:'/auth/login', data:{username:'new_manager',password:'custom-pass'},
  })
  assert.equal(api.login({username:'safety',password:'admin123',role:'safety'}).data.password, 'admin123')
})

test('runtime presentation toggle persists and never deletes showcase assets', async () => {
  const values = new Map()
  globalThis.localStorage = { getItem:k=>values.get(k) ?? null, setItem:(k,v)=>values.set(k,v) }
  globalThis.document = { documentElement:{ dataset:{} } }
  const source = (await readFile(new URL('../src/utils/preferences.js', import.meta.url),'utf8'))
    .replace("import { ref } from 'vue'", 'const ref = value => ({value})')
    .replace('import.meta.env.VITE_ENABLE_PRESENTATION_ASSETS', 'undefined')
  const prefs = await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))
  assert.equal(prefs.presentationEnabled(),true)
  prefs.setPresentationAssets(false)
  assert.equal(prefs.presentationEnabled(),false)
  assert.equal(values.get('znt_presentation_assets'),'false')
  prefs.setPresentationAssets(true)
  prefs.setWorkspaceStyle('showcase')
  assert.equal(document.documentElement.dataset.workspaceStyle,'showcase')
  assert.equal(prefs.presentationEnabled(),true)
})
