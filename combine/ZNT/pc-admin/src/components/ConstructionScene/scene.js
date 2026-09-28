import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

// Procedural illustration only: no survey coordinates, external maps or BIM inference.
export function createConstructionScene(host, { onLabels, onFailure, dark = true }) {
  const scene = new THREE.Scene()
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'low-power' })
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5))
  host.appendChild(renderer.domElement)
  renderer.domElement.setAttribute('aria-label', '工地三维示意，左键旋转、右键平移、滚轮缩放')
  const camera = new THREE.PerspectiveCamera(42, 1, 1, 800)
  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.minDistance = 55
  controls.maxDistance = 350
  controls.maxPolarAngle = Math.PI * .49
  controls.autoRotateSpeed = .45
  scene.add(new THREE.HemisphereLight(0xe7f7ff, 0x415268, 2.2))
  const sunlight = new THREE.DirectionalLight(0xffffff, 2)
  sunlight.position.set(60, 120, 80); scene.add(sunlight)
  const solids = new THREE.Group(); scene.add(solids)
  const mats = {
    concrete: new THREE.MeshStandardMaterial({ color: 0x91a9b9, roughness: .8 }),
    steel: new THREE.MeshStandardMaterial({ color: 0x527687, roughness: .65 }),
    ground: new THREE.MeshStandardMaterial({ color: 0x213444, roughness: 1 }),
    road: new THREE.MeshStandardMaterial({ color: 0x344956, roughness: 1 }),
    crane: new THREE.MeshStandardMaterial({ color: 0xd5a65b }),
    green: new THREE.MeshStandardMaterial({ color: 0x3d887d }),
    pit: new THREE.MeshStandardMaterial({ color: 0x101e29 }),
  }
  function box(x,y,z,w,h,d,material=mats.concrete) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material)
    mesh.position.set(x,y,z); solids.add(mesh); return mesh
  }
  function beam(a,b,r=.35,material=mats.steel) {
    const start=new THREE.Vector3(...a),end=new THREE.Vector3(...b),delta=end.clone().sub(start)
    const mesh=new THREE.Mesh(new THREE.CylinderGeometry(r,r,delta.length(),5),material)
    mesh.position.copy(start.add(end).multiplyScalar(.5))
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize())
    solids.add(mesh)
  }
  box(0,-2,0,180,4,140,mats.ground)
  box(0,.1,42,168,.25,13,mats.road)
  box(62,.1,-6,12,.25,108,mats.road)
  // Main structure: slabs, open columns and scaffolding.
  for(let floor=0;floor<5;floor++){
    box(-34,1+floor*10,-23,49,1.2,37)
    for(const x of [-54,-34,-14]) for(const z of [-38,-8]) box(x,6+floor*10,z,1.8,9,1.8)
  }
  for(let x=-61;x<=-5;x+=8) {
    beam([x,0,-45],[x,47,-45],.25)
    for(let y=5;y<48;y+=8) beam([x,y,-45],[Math.min(x+8,-5),y+8,-45],.18)
  }
  for(let y=5;y<48;y+=8) beam([-61,y,-45],[-5,y,-45],.22)
  // Crane with suspended block, not an inferred live lifting event.
  box(1,29,-30,2.2,58,2.2,mats.crane)
  box(10,58,-30,66,1.8,2,mats.crane)
  beam([1,68,-30],[-23,58,-30],.3,mats.crane)
  beam([1,68,-30],[42,58,-30],.3,mats.crane)
  beam([30,58,-30],[30,18,-30],.13)
  box(30,15,-30,10,5,7,mats.concrete)
  // Excavation illustrated by a dark inset with perimeter rails.
  box(26,.3,12,37,.4,28,mats.pit)
  for(const z of [-3,27]) {
    beam([6,3,z],[46,3,z],.3,mats.crane)
    for(let x=6;x<=46;x+=8) beam([x,0,z],[x,4,z],.3,mats.crane)
  }
  for(const x of [6,46]) beam([x,3,-3],[x,3,27],.3,mats.crane)
  // Material stacks, processing shelter, entry gate, perimeter.
  for(let i=0;i<4;i++) box(33+i*6,2,-52,4,4,12,mats.steel)
  box(-36,12,18,36,1,20,mats.green)
  for(const x of [-52,-20]) for(const z of [10,26]) box(x,6,z,1,12,1,mats.steel)
  box(-68,4,54,12,8,10)
  beam([-77,6,40],[-53,6,40],.3,mats.crane)
  for(const z of [-67,67]) box(0,2,z,177,4,.8,mats.steel)
  for(const x of [-88,88]) box(x,2,0,.8,4,134,mats.steel)
  const grid=new THREE.GridHelper(180,18,0x527184,0x314956); grid.position.y=.05; scene.add(grid)
  let markers=[],running=true,visible=true,lost=false,frame=0,last=0
  function theme(isDark){
    scene.background=new THREE.Color(isDark?0x08152b:0xf1f0e9)
    const colors=isDark
      ? {ground:0x172e4c,road:0x294363,concrete:0x8da9cc,steel:0x476589,crane:0xbba267,green:0x405f82,pit:0x060f20}
      : {ground:0xdad8cd,road:0xaaa99f,concrete:0xc4c3b9,steel:0x5a5a54,crane:0x77776f,green:0x696963,pit:0x30302e}
    for(const [key,value] of Object.entries(colors))mats[key].color.setHex(value)
    scene.children.find(o=>o.isHemisphereLight)?.color.setHex(isDark?0xe7f1ff:0xffffff)
    scene.children.find(o=>o.isHemisphereLight)?.groundColor.setHex(isDark?0x415268:0x65655f)
    grid.material.color.setHex(isDark?0x668bb5:0x74746c)
  }
  function view(type='overview'){
    controls.target.set(0,10,0)
    camera.position.set(...(type==='top'?[0,230,.5]:[156,139,170]))
    controls.update()
  }
  function resize(){const {width,height}=host.getBoundingClientRect();if(!width||!height)return;renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix()}
  function render(time){
    if(!running)return
    frame=requestAnimationFrame(render)
    if(!visible||document.hidden||lost||time-last<33)return
    last=time;controls.update();renderer.render(scene,camera)
    const width=host.clientWidth,height=host.clientHeight
    onLabels(markers.map(m=>{
      const p=new THREE.Vector3(...m.position).project(camera)
      return {...m,left:(p.x+1)*width/2,top:(1-p.y)*height/2,visible:p.z>=-1&&p.z<=1&&Math.abs(p.x)<.96&&Math.abs(p.y)<.94}
    }))
  }
  const resizeObserver=new ResizeObserver(resize);resizeObserver.observe(host)
  const intersectionObserver=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting});intersectionObserver.observe(host)
  function contextLost(event){event.preventDefault();lost=true;onFailure('三维渲染已暂停，可使用右侧点位列表；重新进入页面可重试。')}
  renderer.domElement.addEventListener('webglcontextlost',contextLost)
  theme(dark);view();resize();frame=requestAnimationFrame(render)
  return {
    view, theme,
    setMarkers(value){markers=value},
    setOrbit(value){controls.autoRotate=Boolean(value)&&!matchMedia('(prefers-reduced-motion: reduce)').matches},
    zoom(factor){const offset=camera.position.clone().sub(controls.target);offset.multiplyScalar(factor);offset.setLength(Math.max(55,Math.min(350,offset.length())));camera.position.copy(controls.target).add(offset);controls.update()},
    dispose(){
      running=false;cancelAnimationFrame(frame);resizeObserver.disconnect();intersectionObserver.disconnect();controls.dispose()
      renderer.domElement.removeEventListener('webglcontextlost',contextLost)
      const geometries=new Set(),materials=new Set()
      scene.traverse(o=>{if(o.geometry)geometries.add(o.geometry);if(o.material)(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>materials.add(m))})
      geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose())
      renderer.dispose();renderer.forceContextLoss();renderer.domElement.remove()
    },
  }
}
