<template>
  <section ref="root" class="site-overview" aria-label="工地三维总览">
    <header>
      <div><span class="eyebrow">SITE OVERVIEW / 空间总览</span><h2>中建国际投资四川公司 · 智慧工地</h2><p>场地分区 · 固定监控 · 无人机巡检</p></div>
      <div class="header-actions"><a :href="viewerUrl" target="_blank" rel="noopener">独立窗口打开</a><a-button @click="fullscreen">全屏 / 退出</a-button></div>
    </header>
    <div class="viewer-shell">
      <iframe ref="viewer" :src="viewerUrl" title="四川公司智慧工地完整交互场景" allow="fullscreen" allowfullscreen @load="checkViewer" />
      <div v-if="failure || !ready" class="viewer-status" role="status">
        <span>{{ failure || '正在加载完整交互场景…' }}</span>
        <a-button v-if="failure" @click="reloadViewer">重新加载</a-button>
      </div>
    </div>
    <p v-if="fullscreenError" class="fullscreen-error" role="status">{{ fullscreenError }}</p>
    <details class="business-points">
      <summary>业务点位与风险 <span>{{ demo ? '展示点位' : '业务点位' }} · {{ points.length }} 个点位</span></summary>
      <div class="business-layout">
        <div>
          <a-select v-model:value="filter" aria-label="点位风险筛选" style="width:100%" :options="filters" />
          <div class="point-list"><button v-for="p in filtered" :key="p.id" :class="{active:selected?.id===p.id}" @click="selected=p"><span class="dot" :class="p.riskLevel"></span><span>{{ p.name }}</span><small>{{ p.riskCount ?? '—' }} 项</small></button><p v-if="!filtered.length">当前筛选下无点位。</p></div>
        </div>
        <div class="point-detail">
          <template v-if="selected"><strong>{{ selected.name }}</strong><p>{{ demo ? '示例点位与计数，不代表实时监控状态。' : '业务来源点位；位置尚未映射到三维模型。' }}</p><a-button :disabled="!selected.cameraId" @click="$emit('point-click',selected)">查看该摄像头</a-button><p v-if="!selected.cameraId">尚未关联摄像头。</p></template>
          <p v-else>选择业务点位，查看风险数量及关联摄像头。</p>
          <router-link to="/detection-results">打开检测结果与证据 →</router-link>
        </div>
      </div>
    </details>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
const props = defineProps({ points: { type: Array, default: () => [] }, demo: Boolean })
defineEmits(['point-click'])
const viewerUrl = `${import.meta.env.BASE_URL}3D/中建国际投资四川公司-交互预览.html`
const root = ref(), viewer = ref(), ready = ref(false), failure = ref(''), fullscreenError = ref('')
const selected = ref(null), filter = ref('all')
const filters = [{label:'全部点位',value:'all'},{label:'高危点位',value:'red'},{label:'中危点位',value:'orange'},{label:'低危点位',value:'yellow'},{label:'无已标注风险',value:'green'}]
const filtered = computed(() => props.points.filter(p => filter.value === 'all' || p.riskLevel === filter.value))
watch([filtered, () => props.demo], () => { selected.value = null })
let timer, disposed = false
function checkViewer() {
  clearTimeout(timer)
  const deadline = Date.now() + 30000
  function check() {
    if (disposed) return
    try {
      const state = viewer.value?.contentWindow?.site3D?.getState()
      if (state?.frames >= 3) { ready.value = true; failure.value = ''; return }
    } catch { /* A load error is reported below after the startup deadline. */ }
    if (Date.now() >= deadline) { failure.value = '交互场景未能启动，请重新加载或使用独立窗口打开。'; return }
    timer = setTimeout(check, 200)
  }
  check()
}
function reloadViewer() {
  clearTimeout(timer); ready.value = false; failure.value = ''
  viewer.value.src = viewerUrl
}
async function fullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen()
    else await root.value.requestFullscreen()
    fullscreenError.value = ''
  } catch { fullscreenError.value = '当前窗口不支持全屏，可使用独立窗口打开。' }
}
onBeforeUnmount(() => { disposed = true; clearTimeout(timer) })
</script>

<style scoped>
.site-overview{border:1px solid var(--border-color);border-radius:16px;overflow:hidden;background:var(--surface);margin:0 0 20px;color:var(--text-primary)}
header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:22px 24px}.eyebrow{font-size:11px;letter-spacing:2px;color:var(--link)}h2{font-size:24px;margin:6px 0}header p,.point-detail p,.point-list p{color:var(--text-secondary);font-size:13px;line-height:1.7;margin:5px 0}.header-actions{display:flex;align-items:center;gap:14px;flex-shrink:0}.header-actions a{font-size:13px}
.viewer-shell{position:relative;height:760px;background:#071323}iframe{display:block;border:0;width:100%;height:100%}.viewer-status{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:15px;background:#071323;color:#eaf4ff}.fullscreen-error{padding:0 24px;color:var(--text-secondary);font-size:13px}
.business-points{border-top:1px solid var(--border-color);padding:16px 24px}.business-points summary{cursor:pointer;font-size:14px}.business-points summary span{font-size:12px;color:var(--text-secondary);margin-left:12px}.business-layout{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:16px}.point-list{max-height:220px;overflow:auto;margin:12px 0}.point-list button{display:flex;align-items:center;width:100%;gap:8px;text-align:left;border:1px solid transparent;background:transparent;color:var(--text-primary);padding:10px 7px;cursor:pointer;font:inherit;font-size:13px;border-radius:6px}.point-list button.active,.point-list button:hover{background:var(--primary-soft);border-color:var(--border-color)}.point-list small{margin-left:auto}.dot{width:7px;height:7px;flex-shrink:0;border-radius:50%;background:var(--info)}.dot.red{background:var(--danger)}.dot.orange{background:var(--warning)}.dot.yellow{background:var(--caution)}.dot.green{background:var(--success)}.point-detail a{display:inline-block;font-size:13px;margin-top:12px}
.site-overview:fullscreen{display:flex;flex-direction:column;border-radius:0;overflow:auto}.site-overview:fullscreen header{padding:10px 20px}.site-overview:fullscreen h2{font-size:18px}.site-overview:fullscreen header p,.site-overview:fullscreen .eyebrow{display:none}.site-overview:fullscreen .viewer-shell{flex:1;min-height:0}.site-overview:fullscreen .business-points{display:none}
@media(max-width:900px){header{padding:16px;flex-wrap:wrap}h2{font-size:20px}.viewer-shell{height:760px}.business-layout{grid-template-columns:1fr}.business-points{padding:16px}}
</style>
