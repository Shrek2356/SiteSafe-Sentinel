<template>
  <div class="runtime-strip" aria-live="polite">
    <span class="runtime-title">运行状态</span>
    <a-badge :status="business ? 'success' : 'error'" :text="business ? '业务在线' : '业务未连接'" />
    <a-badge :status="detect.online ? 'success' : 'error'" :text="detect.online ? '检测桥在线' : '检测桥未连接'" />
    <span>队列 {{ detect.inference_queue?.pending ?? '—' }}</span>
    <span>{{ offlineReady ? '离线配置齐备 · 按需加载' : '离线模型待配置' }}</span>
    <a-tag :color="presentationAssets ? 'gold' : 'blue'">{{ presentationAssets ? '含预置展示素材' : '仅接口数据' }}</a-tag>
    <span class="runtime-time">{{ updated || '检查中…' }}</span>
    <a-button size="small" type="text" :loading="loading" @click="refresh">刷新</a-button>
    <router-link to="/task-center">任务中心 →</router-link>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { checkDetectHealth } from '@/api/detect'
import { getBusinessApiBase } from '@/utils/endpoints'
import { presentationAssets } from '@/utils/preferences'
const business = ref(false), detect = ref({}), loading = ref(false), updated = ref('')
const offlineReady = computed(() => detect.value.profiles?.some(p => p.id === 'offline' && p.ready))
let timer, disposed = false
async function refresh() {
  if (loading.value || disposed) return
  clearTimeout(timer)
  loading.value = true
  const [b, d] = await Promise.allSettled([
    axios.get(`${getBusinessApiBase()}/health`, { timeout: 5000 }), checkDetectHealth(),
  ])
  if (disposed) return
  business.value = b.status === 'fulfilled' && b.value.data?.ok === true && b.value.data?.service === 'znt-business-api'
  detect.value = d.status === 'fulfilled' ? d.value : {}
  updated.value = new Date().toLocaleTimeString()
  loading.value = false
  timer = setTimeout(refresh, 15000)
}
onMounted(refresh)
onBeforeUnmount(() => { disposed = true; clearTimeout(timer) })
</script>
<style scoped>
.runtime-strip { display:flex; align-items:center; gap:16px; flex-wrap:wrap; padding:10px 20px; background:var(--surface); border-bottom:1px solid var(--border-color); color:var(--text-secondary); font-size:12px; }
.runtime-title { color:var(--text-primary); font-weight:600; }
.runtime-time { margin-left:auto; font-variant-numeric:tabular-nums; }
</style>
