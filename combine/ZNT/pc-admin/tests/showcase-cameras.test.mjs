import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { withShowcaseImage, showcaseCameraCases } from '../src/utils/showcaseCameras.js'

test('eight examples have unique camera links and no invented masks', () => {
  assert.deepEqual(Object.values(showcaseCameraCases).sort(), [1,2,3,4,5,6,7,8])
  const item = withShowcaseImage({id:'cam-01',streamUrl:'',online:false,masks:[{x:30}]})
  assert.equal(item.exampleCaseId,2)
  assert.equal(item.online,false)
  assert.deepEqual(item.masks,[])
  assert.equal(item.exampleJobId,'')
})
test('real streams are never replaced by illustrative photos', () => {
  const camera = {id:'cam-01',streamUrl:'https://camera/video.mp4'}
  assert.equal(withShowcaseImage(camera),camera)
})
test('only completed reruns can label an image as a model result', () => {
  const camera = {id:'cam-06',streamUrl:''}
  const manifest = {cases:[{case:8,status:'error',job_id:'failed',overlay:'/bad.png'}]}
  assert.equal(withShowcaseImage(camera,manifest).exampleJobId,'')
  manifest.cases[0] = {case:8,status:'done',job_id:'actual',overlay:'/showcase/latest/case8_overlay.png'}
  assert.equal(withShowcaseImage(camera,manifest).exampleJobId,'actual')
})

test('job links include offline reruns instead of filtering them out as non-live', async () => {
  const source = await readFile(new URL('../src/views/detection-results/index.vue', import.meta.url),'utf8')
  assert.equal(/else if \(route.query.job\)\s*\{\s*filter.value = 'live'/.test(source),false)
})
