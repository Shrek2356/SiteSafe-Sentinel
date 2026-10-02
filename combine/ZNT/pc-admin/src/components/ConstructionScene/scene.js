import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'

const MODEL_URL = `${import.meta.env.BASE_URL}3D/中建国际投资四川公司-智慧工地.glb`

export function createConstructionScene(host, { onLabels, onFailure, onReady, dark = true }) {
  const scene = new THREE.Scene()
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'low-power' })
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5))
  host.appendChild(renderer.domElement)
  renderer.domElement.setAttribute('aria-label', '中建国际投资四川公司智慧工地，左键旋转、右键平移、滚轮缩放')
  const camera = new THREE.PerspectiveCamera(42, 1, .1, 2000)
  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.maxPolarAngle = Math.PI * .49
  controls.autoRotateSpeed = .45
  const hemisphere = new THREE.HemisphereLight(0xe7f7ff, 0x415268, 2.2)
  const sunlight = new THREE.DirectionalLight(0xffffff, 2)
  sunlight.position.set(60, 120, 80)
  scene.add(hemisphere, sunlight)
  const bounds = new THREE.Box3()
  const fitPoints = []
  let model, mixer, markers = [], running = true, visible = true, lost = false, frame = 0, last = 0

  function release(object) {
    const geometries = new Set(), materials = new Set(), textures = new Set(), images = new Set()
    object.traverse(o => {
      if (o.geometry) geometries.add(o.geometry)
      if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => materials.add(m))
    })
    materials.forEach(m => Object.values(m).forEach(v => { if (v?.isTexture) textures.add(v) }))
    textures.forEach(t => { if (t.source?.data) images.add(t.source.data); t.dispose() })
    images.forEach(image => image.close?.())
    geometries.forEach(g => g.dispose())
    materials.forEach(m => m.dispose())
  }

  function theme(isDark) {
    scene.background = new THREE.Color(isDark ? 0x08152b : 0xf1f0e9)
    hemisphere.color.setHex(isDark ? 0xe7f1ff : 0xffffff)
    hemisphere.groundColor.setHex(isDark ? 0x415268 : 0x65655f)
  }

  function view(type = 'overview') {
    if (!model) return
    const center = bounds.getCenter(new THREE.Vector3())
    center.y = bounds.min.y + (bounds.max.y - bounds.min.y) * .22
    const direction = new THREE.Vector3(...(type === 'top' ? [0, 1, .001] : [1, .86, 1.12])).normalize()
    const right = new THREE.Vector3().crossVectors(camera.up, direction).normalize()
    const up = new THREE.Vector3().crossVectors(direction, right)
    const tanV = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))
    const tanH = tanV * camera.aspect
    let distance = 0
    for (const point of fitPoints) {
      const p = point.clone().sub(center)
      distance = Math.max(distance, p.dot(direction) + Math.abs(p.dot(right)) / tanH,
        p.dot(direction) + Math.abs(p.dot(up)) / tanV)
    }
    const size = bounds.getSize(new THREE.Vector3()).length()
    controls.minDistance = size * .12
    controls.maxDistance = Math.max(size * 5, distance * 2)
    // Flush residual damping before resetting to the fitted view.
    controls.enableDamping = false
    controls.update()
    controls.target.copy(center)
    camera.position.copy(center).addScaledVector(direction, distance * 1.12)
    camera.near = Math.max(.05, size / 3000)
    camera.far = Math.max(2000, controls.maxDistance * 4)
    camera.updateProjectionMatrix()
    controls.update()
    controls.enableDamping = true
  }

  function resize() {
    const { width, height } = host.getBoundingClientRect()
    if (!width || !height) return
    renderer.setSize(width, height)
    camera.aspect = width / height
    camera.updateProjectionMatrix()
  }

  function render(time) {
    if (!running) return
    frame = requestAnimationFrame(render)
    if (!visible || document.hidden || lost) { last = time; return }
    if (time - last < 33) return
    const delta = Math.min((time - last) / 1000, .1)
    last = time
    mixer?.update(delta)
    controls.update()
    renderer.render(scene, camera)
    if (!model) return
    const width = host.clientWidth, height = host.clientHeight
    onLabels(markers.map(m => {
      const p = new THREE.Vector3(...m.position).project(camera)
      return { ...m, left: (p.x + 1) * width / 2, top: (1 - p.y) * height / 2,
        visible: p.z >= -1 && p.z <= 1 && Math.abs(p.x) < .96 && Math.abs(p.y) < .94 }
    }))
  }
  const resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(host)
  const intersectionObserver = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting })
  intersectionObserver.observe(host)
  function contextLost(event) {
    event.preventDefault(); lost = true
    onFailure('三维渲染已暂停，可使用右侧点位列表；重新进入页面可重试。')
  }
  renderer.domElement.addEventListener('webglcontextlost', contextLost)
  theme(dark); resize(); frame = requestAnimationFrame(render)
  new GLTFLoader().load(MODEL_URL, gltf => {
    if (!running) { release(gltf.scene); return }
    model = gltf.scene
    scene.add(model)
    bounds.setFromObject(model)
    model.traverse(object => {
      if (!object.geometry) return
      object.geometry.computeBoundingBox()
      const box = object.geometry.boundingBox
      for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
        fitPoints.push(new THREE.Vector3(x, y, z).applyMatrix4(object.matrixWorld))
      }
    })
    if (bounds.isEmpty()) {
      onFailure('模型中没有可显示的三维对象。')
      return
    }
    if (gltf.animations.length) {
      mixer = new THREE.AnimationMixer(model)
      gltf.animations.forEach(clip => mixer.clipAction(clip).play())
    }
    view()
    onReady?.()
  }, undefined, error => {
    if (!running) return
    console.error('Construction model failed to load', error)
    onFailure('智慧工地模型加载失败，请刷新页面重试。')
  })

  return {
    view, theme,
    setMarkers(value) { markers = value },
    setOrbit(value) { controls.autoRotate = Boolean(value) && !matchMedia('(prefers-reduced-motion: reduce)').matches },
    zoom(factor) {
      if (!model) return
      const offset = camera.position.clone().sub(controls.target).multiplyScalar(factor)
      offset.setLength(THREE.MathUtils.clamp(offset.length(), controls.minDistance, controls.maxDistance))
      camera.position.copy(controls.target).add(offset)
      controls.update()
    },
    dispose() {
      running = false; cancelAnimationFrame(frame)
      resizeObserver.disconnect(); intersectionObserver.disconnect(); controls.dispose()
      renderer.domElement.removeEventListener('webglcontextlost', contextLost)
      if (mixer) { mixer.stopAllAction(); mixer.uncacheRoot(model) }
      release(scene)
      renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove()
    },
  }
}
