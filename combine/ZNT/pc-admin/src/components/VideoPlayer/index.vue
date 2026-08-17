<template>
  <!--
    公共视频播放器（Flv.js）
    【后续对接】传入真实 streamUrl（flv/http-flv）即可播放
    当前无流地址时显示占位画面 + 风险掩码叠加
  -->
  <div class="video-player" ref="wrapRef">
    <video
      v-show="hasStream"
      ref="videoRef"
      class="video-el"
      muted
      autoplay
      controls
    />
    <!-- 无流地址占位 -->
    <div v-if="!hasStream" class="placeholder">
      <div class="cam-name">{{ name || '摄像头' }}</div>
      <div class="cam-hint">{{ online === false ? '设备离线' : '视频流占位 · 待接入 FLV' }}</div>
      <div class="scan-line" />
    </div>
    <!-- 风险掩码叠加层 -->
    <RiskMaskOverlay :masks="masks" />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import flvjs from 'flv.js'
import RiskMaskOverlay from '@/components/RiskMask/index.vue'

const props = defineProps({
  /** flv 流地址，空则占位 */
  streamUrl: { type: String, default: '' },
  name: { type: String, default: '' },
  online: { type: Boolean, default: true },
  /** 掩码列表 [{level,x,y,w,h,label}] */
  masks: { type: Array, default: () => [] },
})

const videoRef = ref(null)
const wrapRef = ref(null)
let flvPlayer = null

const hasStream = computed(() => !!props.streamUrl)

function destroyPlayer() {
  if (flvPlayer) {
    flvPlayer.pause()
    flvPlayer.unload()
    flvPlayer.detachMediaElement()
    flvPlayer.destroy()
    flvPlayer = null
  }
}

function initPlayer() {
  destroyPlayer()
  if (!props.streamUrl || !videoRef.value) return
  if (!flvjs.isSupported()) {
    console.warn('[VideoPlayer] 当前浏览器不支持 flv.js')
    return
  }
  flvPlayer = flvjs.createPlayer({
    type: 'flv',
    url: props.streamUrl,
    isLive: true,
  })
  flvPlayer.attachMediaElement(videoRef.value)
  flvPlayer.load()
  flvPlayer.play().catch(() => {})
}

onMounted(initPlayer)
watch(() => props.streamUrl, initPlayer)
onBeforeUnmount(destroyPlayer)
</script>

<style scoped>
.video-player {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 140px;
  background: #1f1f1f;
  overflow: hidden;
  border-radius: 4px;
}
.video-el {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #1f1f1f;
  color: #bfbfbf;
}
.cam-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #f5f5f5;
}
.cam-hint {
  font-size: 12px;
  opacity: 0.7;
}
.scan-line {
  display: none;
}
</style>
