<template>
  <div class="video-player" ref="wrapRef">
    <video v-show="hasStream && !error" ref="videoRef" class="video-el" muted autoplay controls
      @loadedmetadata="updateRect" @resize="updateRect" @error="error = '视频解码或连接失败，请检查预览地址与编码格式'" />
    <div v-if="showExample" class="example-frame">
      <img :src="showOriginal ? exampleOriginalUrl : exampleImageUrl" :alt="name + '异常示例图'" @error="exampleError = true" />
      <div class="example-caption"><strong>{{ name }} · {{ showOriginal ? '异常示例 · 原图' : exampleLabel }}</strong><span>静态示意，非实时视频；点位为展示关联</span>
        <div><button v-if="exampleImageUrl !== exampleOriginalUrl" @click.stop="showOriginal = !showOriginal">{{ showOriginal ? '查看检测标注' : '查看原图' }}</button>
        <a v-if="exampleJobId" :href="`/showcase/latest/case${exampleCaseId}_report.html`" target="_blank" rel="noopener">查看随包报告快照 →</a>
        <router-link v-else :to="{path:'/detection-results',query:{case:exampleCaseId}}">查看案例报告 →</router-link></div>
      </div>
    </div>
    <div v-else-if="!hasStream || error" class="placeholder">
      <div class="cam-name">{{ name || '摄像头' }}</div>
      <div class="cam-hint">{{ exampleError ? '示例图片加载失败，请检查展示素材' : error || (online === false ? '设备离线' : '暂无预览流 · 检测采集与窗口预览分别配置') }}</div>
    </div>
    <div v-if="hasStream && !error && overlayRect" class="overlay-viewport" :style="overlayStyle">
      <RiskMaskOverlay :masks="masks" />
    </div>
  </div>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import flvjs from 'flv.js'
import RiskMaskOverlay from '@/components/RiskMask/index.vue'
import { containRect } from '@/utils/videoGeometry'
const props = defineProps({
  streamUrl: { type:String, default:'' }, name:{ type:String, default:'' },
  online:{ type:Boolean, default:true }, masks:{ type:Array, default:() => [] },
  exampleImageUrl:{ type:String, default:'' }, exampleOriginalUrl:{ type:String, default:'' },
  exampleLabel:{ type:String, default:'异常示例图' }, exampleCaseId:{ type:Number, default:0 },
  exampleJobId:{ type:String, default:'' },
})
const videoRef = ref(null), wrapRef = ref(null), error = ref(''), overlayRect = ref(null)
let flvPlayer, observer
const hasStream = computed(() => Boolean(props.streamUrl))
const showOriginal = ref(false), exampleError = ref(false)
const showExample = computed(() => !hasStream.value && Boolean(props.exampleImageUrl) && !exampleError.value)
watch(() => props.exampleImageUrl, () => { exampleError.value = false; showOriginal.value = false })
const overlayStyle = computed(() => overlayRect.value
  ? Object.fromEntries(Object.entries(overlayRect.value).map(([k,v]) => [k, v + 'px']))
  : { inset:'0' })
function updateRect() {
  const v = videoRef.value, w = wrapRef.value
  overlayRect.value = v && w ? containRect(w.clientWidth,w.clientHeight,v.videoWidth,v.videoHeight) : null
}
function destroyPlayer() {
  if (flvPlayer) { flvPlayer.destroy(); flvPlayer = null }
  const v = videoRef.value
  if (v) { v.pause(); v.removeAttribute('src'); v.load() }
  overlayRect.value = null
}
function initPlayer() {
  destroyPlayer(); error.value = ''
  const url = props.streamUrl, v = videoRef.value
  if (!url || !v) return
  if (/^(rtsp:|[A-Za-z]:[\\/])/i.test(url)) {
    error.value = '采集地址不能直接预览，请在视频源设置中填写 HTTP 预览流'; return
  }
  if (/\.(mp4|webm|ogg|m3u8)(\?|$)/i.test(url) || /^(blob:|data:)/i.test(url)) {
    if (/\.m3u8(\?|$)/i.test(url) && !v.canPlayType('application/vnd.apple.mpegurl')) {
      error.value = '当前窗口不支持 HLS，请提供 FLV/MP4 预览地址'; return
    }
    v.src = url; v.play().catch(() => {}); return
  }
  if (!flvjs.isSupported()) { error.value = '当前窗口不支持 FLV，请提供 MP4/WebM 预览地址'; return }
  try {
    flvPlayer = flvjs.createPlayer({ type:'flv', url, isLive:true })
    flvPlayer.on(flvjs.Events.ERROR, () => { error.value = 'FLV 预览连接失败；请检查地址、编码和跨域配置' })
    flvPlayer.attachMediaElement(v); flvPlayer.load(); flvPlayer.play().catch(() => {})
  } catch(e) { error.value = e.message || '预览初始化失败' }
}
onMounted(() => { observer = new ResizeObserver(updateRect); observer.observe(wrapRef.value); initPlayer() })
watch(() => props.streamUrl, initPlayer)
onBeforeUnmount(() => { observer?.disconnect(); destroyPlayer() })
</script>
<style scoped>
.video-player { position:relative; width:100%; height:100%; min-height:140px; background:#101820; overflow:hidden; border-radius:6px; }
.video-el { display:block; width:100%; height:100%; object-fit:contain; }
.example-frame { position:absolute; inset:0; display:flex; flex-direction:column; }
.example-frame img { width:100%; flex:1; min-height:0; object-fit:contain; }
.example-caption { flex-shrink:0; padding:7px 10px; background:#0b1930; color:#f0f6ff; font-size:12px; line-height:1.6; }
.example-caption strong,.example-caption span { display:block; }
.example-caption span { color:#abc0dc; }
.example-caption a { color:#a8d4ff; }
.example-caption button { margin-right:12px; color:#f0f6ff; background:#203653; border:1px solid #7594b7; border-radius:4px; cursor:pointer; }
.overlay-viewport { position:absolute; pointer-events:none; }
.placeholder { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px; background:#101820; color:#b8c6d2; }
.cam-name { font-size:14px; font-weight:600; margin-bottom:8px; color:#e2edf5; }
.cam-hint { font-size:12px; text-align:center; line-height:1.7; }
</style>
