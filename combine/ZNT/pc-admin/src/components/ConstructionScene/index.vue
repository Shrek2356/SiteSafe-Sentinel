<template>
  <section ref="root" class="site-overview" aria-label="工地三维总览">
    <header><div><span class="eyebrow">SITE OVERVIEW / 空间总览</span><h2>工地作业区 · 三维示意</h2><p>通用布局演示，不是实测地图或 BIM；风险判断请查看原图与报告。</p></div><a-button @click="fullscreen">全屏 / 退出</a-button></header>
    <div class="scene-layout">
      <div class="viewport">
        <div ref="host" class="canvas-host" />
        <div class="scene-caption">主体结构 / 塔吊 / 基坑 / 加工棚 / 材料区 / 出入口</div>
        <div class="pins"><button v-for="p in labels.filter(p=>p.visible)" :key="p.id" :style="{left:p.left+'px',top:p.top+'px'}" :class="['pin',p.riskLevel,{selected:selected?.id===p.id}]" @click="selected=p">{{ p.name }} <span>{{ p.riskCount ?? '—' }}</span></button></div>
        <div v-if="failure" class="fallback" role="status">{{ failure }}</div>
        <div v-else-if="!ready" class="fallback" role="status">加载本地三维场景…</div>
        <div class="scene-controls"><a-button @click="scene?.view()">总览复位</a-button><a-button @click="scene?.view('top')">俯视</a-button><a-button aria-label="放大三维场景" @click="scene?.zoom(.8)">＋</a-button><a-button aria-label="缩小三维场景" @click="scene?.zoom(1.25)">−</a-button><a-checkbox v-model:checked="orbit">自动旋转</a-checkbox></div>
        <div class="gesture">拖动旋转 · 右键平移 · 滚轮缩放</div>
      </div>
      <aside>
        <div class="point-heading"><strong>点位与风险</strong><span>{{ demo ? '展示点位' : '业务点位' }}</span></div>
        <p v-if="!demo">尚未配置经核验的三维坐标，业务点位仅列于下方，不自动投影。</p>
        <a-select v-model:value="filter" aria-label="点位风险筛选" style="width:100%" :options="filters" />
        <div class="point-list"><button v-for="p in filtered" :key="p.id" :class="{active:selected?.id===p.id}" @click="selected=p"><span class="dot" :class="p.riskLevel"></span><span>{{ p.name }}</span><small>{{ p.riskCount ?? '—' }} 项</small></button><p v-if="!filtered.length">当前筛选下无点位。</p></div>
        <div v-if="selected" class="point-detail"><strong>{{ selected.name }}</strong><p>{{ demo ? '示例布局与示例计数，不代表实时监控状态。' : '业务来源点位；位置尚未映射到三维模型。' }}</p><a-button :disabled="!selected.cameraId" @click="$emit('point-click',selected)">查看该摄像头</a-button><p v-if="!selected.cameraId">尚未关联摄像头。</p></div>
        <router-link to="/detection-results">打开检测结果与证据 →</router-link>
      </aside>
    </div>
  </section>
</template>
<script setup>
import { computed,onMounted,onBeforeUnmount,ref,watch } from 'vue'
import { colorTheme } from '@/utils/theme'
import { sceneMarkers } from './markers'
const props=defineProps({points:{type:Array,default:()=>[]},demo:Boolean})
defineEmits(['point-click'])
const root=ref(),host=ref(),labels=ref([]),selected=ref(null),filter=ref('all'),orbit=ref(false),failure=ref(''),ready=ref(false)
const filters=[{label:'全部点位',value:'all'},{label:'高危点位',value:'red'},{label:'中危点位',value:'orange'},{label:'低危点位',value:'yellow'},{label:'无已标注风险',value:'green'}]
const filtered=computed(()=>props.points.filter(p=>filter.value==='all'||p.riskLevel===filter.value))
let scene,disposed=false
function update(){scene?.setMarkers(sceneMarkers(filtered.value,props.demo));labels.value=[];selected.value=null}
watch([filtered,()=>props.demo],update)
watch(orbit,v=>scene?.setOrbit(v))
watch(colorTheme,v=>scene?.theme(v==='dark'))
async function fullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await root.value.requestFullscreen()}catch{failure.value='当前窗口不支持全屏，仍可旋转和缩放。'}}
onMounted(async()=>{
  try{
    const {createConstructionScene}=await import('./scene')
    if(disposed)return
    scene=createConstructionScene(host.value,{dark:colorTheme.value==='dark',onLabels:v=>{labels.value=v},onFailure:v=>{failure.value=v;labels.value=[]}})
    ready.value=true;update()
  }catch{failure.value='当前设备不支持三维渲染；点位列表和摄像头入口仍可使用。'}
})
onBeforeUnmount(()=>{disposed=true;scene?.dispose()})
</script>
<style scoped>
.site-overview{border:1px solid var(--border-color);border-radius:16px;overflow:hidden;background:var(--surface);margin:0 0 20px;color:var(--text-primary)}header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:22px 24px}.eyebrow{font-size:11px;letter-spacing:2px;color:var(--link)}h2{font-size:24px;margin:6px 0}header p,aside p{color:var(--text-secondary);font-size:13px;line-height:1.7;margin:5px 0}.scene-layout{display:grid;grid-template-columns:minmax(0,1fr) 270px}.viewport{height:490px;position:relative;overflow:hidden;background:var(--bg-2)}.canvas-host{position:absolute;inset:0}.scene-caption{position:absolute;left:18px;top:16px;background:var(--surface);padding:6px 12px;border-radius:6px;font-size:12px;pointer-events:none}.pins{position:absolute;inset:0;pointer-events:none}.pin{position:absolute;transform:translate(-50%,-100%);border:1px solid var(--border-color);border-left:4px solid var(--info);border-radius:5px;padding:5px 8px;background:var(--surface);color:var(--text-primary);cursor:pointer;pointer-events:auto;font:inherit;font-size:12px;box-shadow:var(--shadow-card)}.pin span{margin-left:6px}.pin.red{border-left-color:var(--danger)}.pin.orange{border-left-color:var(--warning)}.pin.yellow{border-left-color:var(--caution)}.pin.green{border-left-color:var(--success)}.pin.selected{outline:2px solid var(--primary);z-index:2}.scene-controls{position:absolute;bottom:32px;left:16px;right:16px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;background:var(--surface);width:fit-content;padding:6px;border-radius:8px}.gesture{position:absolute;bottom:8px;left:20px;font-size:11px;color:var(--text-secondary)}.fallback{position:absolute;top:70px;left:20px;right:20px;padding:18px;background:var(--surface);border:1px solid var(--border-color);border-radius:8px}aside{padding:18px;border-left:1px solid var(--border-color);min-width:0}.point-heading{display:flex;justify-content:space-between;margin-bottom:12px}.point-heading span{font-size:11px;color:var(--text-muted)}.point-list{max-height:215px;overflow:auto;margin:12px 0}.point-list button{display:flex;align-items:center;width:100%;gap:8px;text-align:left;border:1px solid transparent;background:transparent;color:var(--text-primary);padding:10px 7px;cursor:pointer;font:inherit;font-size:13px;border-radius:6px}.point-list button.active,.point-list button:hover{background:var(--primary-soft);border-color:var(--border-color)}.point-list small{margin-left:auto}.dot{width:7px;height:7px;flex-shrink:0;border-radius:50%;background:var(--info)}.dot.red{background:var(--danger)}.dot.orange{background:var(--warning)}.dot.yellow{background:var(--caution)}.dot.green{background:var(--success)}.point-detail{border-top:1px solid var(--border-color);padding:12px 0}aside>a{font-size:13px}.site-overview:fullscreen{overflow:auto;border-radius:0}.site-overview:fullscreen .viewport{height:calc(100vh - 130px)}@media(max-width:900px){.scene-layout{grid-template-columns:1fr}.viewport{height:400px}aside{border-left:0;border-top:1px solid var(--border-color)}header{padding:16px}.point-list{max-height:150px}}
</style>
