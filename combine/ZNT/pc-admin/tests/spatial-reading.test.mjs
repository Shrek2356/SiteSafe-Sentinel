import { test } from 'node:test'
import assert from 'node:assert/strict'
import { sceneMarkers } from '../src/components/ConstructionScene/markers.js'
import { readStoredObject } from '../src/utils/safeStorage.js'
import { normalizeFontPercent,constrainView,zoomAt } from '../src/utils/readingGeometry.js'
import { scaleFontValue } from '../scripts/fontScale.js'
test('real points never acquire invented scene coordinates',()=>{
  assert.deepEqual(sceneMarkers([{id:'real',x:30,y:50}],false),[])
})
test('only explicitly mapped demo zones project into the scene',()=>{
  const result=sceneMarkers([{id:'a',name:'基坑B区'},{id:'b',name:'未配置区域',x:50,y:50}],true)
  assert.equal(result.length,1);assert.deepEqual(result[0].position,[0,2,9]);assert.equal(result[0].source,'presentation')
})
test('corrupt or non-object local cache cannot crash startup',()=>{
  for(const value of ['bad','[]','1','null','"abc"'])assert.equal(readStoredObject('x',{getItem:()=>value}),null)
  assert.deepEqual(readStoredObject('x',{getItem:()=>'{"id":"a"}'}),{id:'a'})
  assert.equal(readStoredObject('x',{getItem:()=>{throw Error('blocked')}}),null)
})
test('reading size clamps and zoom preserves viewport bounds',()=>{
  assert.equal(normalizeFontPercent(500),200);assert.equal(normalizeFontPercent('bad'),100)
  assert.deepEqual(constrainView({scale:2,x:-5000,y:10},800,600),{scale:2,x:-800,y:0})
  assert.deepEqual(zoomAt({scale:1,x:0,y:0},2,{x:400,y:300},800,600),{scale:2,x:-400,y:-300})
})
test('font scaling changes typography only and exactly once',()=>{
  assert.equal(scaleFontValue('width','40px'),'40px')
  const scaled=scaleFontValue('font-size','14px');assert.match(scaled,/--ui-font-scale/)
  assert.equal(scaleFontValue('font-size',scaled),scaled)
})
