<template>
  <!--
    ① 首页数字驾驶舱
    业务：指标总览 + 平面点位 + 高危视频轮播 + 右侧图表看板 + 底部快捷操作
  -->
  <div class="dashboard">
    <!-- 队形象横幅：嘉然今天也在守护工地 -->
    <div class="team-banner" :key="projectKey">
      <img class="mascot left" :src="JR.mascot1" alt="嘉然" />
      <div class="team-copy">
        <div class="team-name">{{ TEAM_NAME }}</div>
        <div class="team-sub">工地安全智能检测系统 · 数字驾驶舱</div>
        <div class="project-chip">
          <span class="project-chip-label">当前项目</span>
          <span class="project-chip-name">{{ projectTitle }}</span>
          <span v-if="projectAddress" class="project-chip-addr">{{ projectAddress }}</span>
        </div>
        <div class="mood-legend">
          <span><img :src="JR.yes" alt="" />待处理</span>
          <span><img :src="JR.emergent" alt="" />紧急事项</span>
          <span><img :src="JR.no" alt="" />正常</span>
        </div>
      </div>
      <img class="mascot right" :src="JR.mascot2" alt="嘉然" />
    </div>

    <!-- 顶部指标栏（可点击查看明细） -->
    <a-row :gutter="12" class="metrics" :class="{ 'metrics-flash': dataFlash }">
      <a-col v-for="m in metrics" :key="projectKey + '-' + m.key" :span="4" style="flex: 1; max-width: 20%">
        <a-tooltip :title="m.tip || '点击查看明细'">
          <div class="metric-card clickable" :class="'t-' + m.type" @click="onMetricClick(m)">
            <div class="metric-label">
              <span class="label-with-mood">
                <img v-if="metricMood(m.key)" class="mood-mini" :src="metricMood(m.key).src" :alt="metricMood(m.key).tip" />
                {{ m.label }}
              </span>
              <span class="link-hint">查看 ›</span>
            </div>
            <div class="metric-value">
              {{ m.value }}<span class="unit">{{ m.unit }}</span>
            </div>
            <div class="metric-trend">{{ m.trendPrefix ?? '较昨日 ' }}{{ m.trend }}</div>
          </div>
        </a-tooltip>
      </a-col>
    </a-row>

    <a-row :gutter="12" class="main-row">
      <!-- 左侧：工地 2D 平面点位图 -->
      <a-col :span="7">
        <div class="panel">
          <div class="panel-title">
            工地点位风险分布 · {{ projectShort }}
            <span v-if="isPresentationGroup('sitePoints')" class="presentation-tag">演示素材</span>
          </div>
          <SiteMap :points="sitePoints" style="height: 360px" @point-click="onPointClick" />
        </div>
      </a-col>

      <!-- 中间：高风险轮播（成果图占位，streamUrl 预留） -->
      <a-col :span="9">
        <div class="panel">
          <div class="panel-title">
            高风险视频轮播
            <span class="sub-tip">当前展示检测结果图 · 视频流接口已预留</span>
            <span v-if="isPresentationGroup('highRiskVideos')" class="presentation-tag">演示素材</span>
          </div>
          <a-carousel autoplay :dots="true" class="video-carousel">
            <div v-for="v in videos" :key="v.id" class="carousel-item">
              <!-- 有流地址则播流；否则展示成果标注图 -->
              <div v-if="v.streamUrl" class="stream-wrap">
                <VideoPlayer :name="v.cameraName + ' · ' + v.title" :stream-url="v.streamUrl" :masks="getMasks(v)" />
              </div>
              <div
                v-else
                class="cover-wrap"
                @click="openVideoCase(v)"
              >
                <img v-if="v.cover" :src="v.cover" :alt="v.title" />
                <div v-else class="cover-empty">结果图占位</div>
                <div class="cover-badge">检测结果图</div>
              </div>
              <div class="video-caption">
                <a-tag :color="levelColor(v.riskLevel)">{{ levelText(v.riskLevel) }}</a-tag>
                <span>{{ v.title }}</span>
                <span class="time">{{ v.time }}</span>
              </div>
            </div>
          </a-carousel>
        </div>
      </a-col>

      <!-- 右侧：数据看板 -->
      <a-col :span="8">
        <div class="panel charts-panel">
          <div class="panel-title">
            数据看板
            <span v-if="hasPresentationCharts" class="presentation-tag">部分演示数据</span>
          </div>
          <div ref="trendRef" class="chart-box" />
          <div ref="pieRef" class="chart-box" />
          <div class="rank-box">
            <div class="sub-title">班组整改排行</div>
            <div v-for="(t, i) in teamRank" :key="t.name" class="rank-item">
              <span class="rank-no">{{ i + 1 }}</span>
              <span class="rank-name">{{ t.name }}</span>
              <a-progress
                :percent="t.rate"
                size="small"
                :stroke-color="'#f26a57'"
                :trail-color="'#f7e3d7'"
                style="flex: 1; margin: 0 8px"
              />
              <span>{{ t.fixed }}/{{ t.total }}</span>
            </div>
          </div>
          <div class="top-box">
            <div class="sub-title">高频隐患 TOP5</div>
            <div v-for="(h, i) in topHazards" :key="h.name" class="top-item">
              <span>{{ i + 1 }}. {{ h.name }}</span>
              <a-badge :count="h.count" :number-style="{ backgroundColor: '#f26a57' }" />
            </div>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- 底部快捷操作栏 -->
    <div class="quick-bar">
      <a-space>
        <a-button type="primary" @click="$router.push('/monitor')">打开实时监控</a-button>
        <a-button @click="$router.push('/realtime-detect')">实时检测</a-button>
        <a-button @click="$router.push({ path: '/workorder', query: { status: 'pending' } })">处置待办工单</a-button>
        <a-button @click="$router.push('/analysis')">查看复盘报告</a-button>
        <a-button @click="$router.push('/detection-results')">检测结果汇总</a-button>
        <a-button @click="$router.push('/realtime-detect')">启动真实 AI 检测</a-button>
      </a-space>
    </div>

  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { message } from 'ant-design-vue'
import SiteMap from '@/components/SiteMap/index.vue'
import VideoPlayer from '@/components/VideoPlayer/index.vue'
import { fetchDashboardData } from '@/api/dashboard'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { JR, TEAM_NAME, metricMood } from '@/utils/jr'
import { subscribeModules } from '@/utils/moduleBus'
import { colorTheme } from '@/utils/theme'

const router = useRouter()
const userStore = useUserStore()
const metrics = ref([])
const sitePoints = ref([])
const videos = ref([])
const teamRank = ref([])
const topHazards = ref([])
const riskTrend = ref({ hours: [], values: [] })
const hazardTypes = ref([])
const projectMeta = ref({ id: '', shortName: '', address: '' })
const presentationAssetGroups = ref([])
const dataFlash = ref(false)
let flashTimer = null

const projectKey = computed(() => userStore.project?.id || 'proj-001')
const projectTitle = computed(() => userStore.project?.name || projectMeta.value.shortName || '未选择项目')
const projectShort = computed(() => projectMeta.value.shortName || userStore.project?.name || '当前项目')
const projectAddress = computed(() => userStore.project?.address || projectMeta.value.address || '')
const hasPresentationCharts = computed(() => (
  ['riskTrendHours', 'hazardTypes', 'teamRank', 'topHazards']
    .some((group) => presentationAssetGroups.value.includes(group))
))


const trendRef = ref(null)
const pieRef = ref(null)
let trendChart = null
let pieChart = null

function levelColor(l) {
  return { red: 'red', orange: 'orange', yellow: 'gold' }[l] || 'default'
}
function levelText(l) {
  return { red: '高危', orange: '中危', yellow: '低危' }[l] || l
}
function getMasks(v) {
  // 轮播项简单映射一级掩码示意
  return [{ level: v.riskLevel, x: 35, y: 25, w: 20, h: 30, label: v.title.split(' - ')[1] || '风险' }]
}

function isPresentationGroup(group) {
  return presentationAssetGroups.value.includes(group)
}

function onPointClick(p) {
  message.info(`跳转监控：${p.name}`)
  router.push({ path: '/monitor', query: { cameraId: p.cameraId } })
}

/** 顶部指标点击跳转明细页 */
function onMetricClick(m) {
  if (!m.link) return
  router.push({ path: m.link, query: m.linkQuery || {} })
}

/** 高风险轮播成果图 → 检测结果对应样例 */
function openVideoCase(v) {
  const query = { filter: 'all' }
  if (v.caseId) query.case = String(v.caseId)
  router.push({ path: '/detection-results', query })
}


function renderCharts() {
  const warmSlice = ['#f26a57', '#f0a14d', '#ffd36b', '#d18d70', '#c85a43']
  const dark = colorTheme.value === 'dark'
  const chartText = dark ? '#dbe6ec' : '#595959'
  const chartGrid = dark ? '#33434f' : '#e8e8e8'

  if (trendRef.value) {
    if (!trendChart) trendChart = echarts.init(trendRef.value)
    trendChart.setOption({
      backgroundColor: 'transparent',
      title: { text: '风险时段分布', textStyle: { fontSize: 13, color: chartText } },
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 16, top: 36, bottom: 24 },
      xAxis: { type: 'category', data: riskTrend.value.hours, axisLabel: { color: chartText }, axisLine: { lineStyle: { color: chartGrid } } },
      yAxis: { type: 'value', minInterval: 1, axisLabel: { color: chartText }, splitLine: { lineStyle: { color: chartGrid } } },
      series: [{
        type: 'line',
        smooth: true,
        data: riskTrend.value.values,
        areaStyle: { opacity: 0.15, color: '#f7c3b4' },
        lineStyle: { color: '#f26a57', width: 2.5 },
        itemStyle: { color: '#f26a57' },
      }],
    }, true)
  }
  if (pieRef.value) {
    if (!pieChart) pieChart = echarts.init(pieRef.value)
    pieChart.setOption({
      backgroundColor: 'transparent',
      title: { text: '隐患类型占比', textStyle: { fontSize: 13, color: chartText } },
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['35%', '60%'],
        data: hazardTypes.value.map((item, index) => ({
          ...item,
          itemStyle: { color: warmSlice[index % warmSlice.length] },
        })),
        label: { fontSize: 11, color: dark ? '#ffc0ad' : '#8a3a30' },
      }],
    }, true)
  }
}

watch(colorTheme, async () => {
  await nextTick()
  renderCharts()
})

async function loadDashboard({ flash = false } = {}) {
  const projectId = userStore.project?.id || 'SITE-DEFAULT'
  const res = await fetchDashboardData({ projectId })
  const d = res.data
  projectMeta.value = {
    id: d.projectId || projectId,
    shortName: d.projectName || '',
    address: d.projectAddress || userStore.project?.address || '',
  }
  metrics.value = d.metrics
  sitePoints.value = d.sitePoints
  videos.value = d.highRiskVideos
  teamRank.value = d.teamRank
  topHazards.value = d.topHazards
  riskTrend.value = d.riskTrendHours
  hazardTypes.value = d.hazardTypes
  presentationAssetGroups.value = Array.isArray(d.presentationAssetGroups)
    ? d.presentationAssetGroups
    : []
  await nextTick()
  renderCharts()
  if (flash) {
    dataFlash.value = true
    clearTimeout(flashTimer)
    flashTimer = setTimeout(() => {
      dataFlash.value = false
    }, 700)
  }
}

watch(
  () => userStore.project?.id,
  async (id, prev) => {
    if (!id || id === prev) return
    await loadDashboard({ flash: true })
  }
)

onMounted(async () => {
  await loadDashboard()
  window.addEventListener('resize', () => {
    trendChart?.resize()
    pieChart?.resize()
  })
})

const unsubModules = subscribeModules(async (detail) => {
  if (detail?.type === 'workorders' || detail?.type === 'detect-results') {
    await loadDashboard({ flash: false })
  }
})

onBeforeUnmount(() => {
  clearTimeout(flashTimer)
  unsubModules()
  trendChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 12px; }
.team-banner {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 10px 18px;
  border-radius: 10px;
  background:
    linear-gradient(110deg, rgba(255, 182, 193, 0.22), color-mix(in srgb, var(--surface) 92%, transparent) 42%, rgba(255, 213, 180, 0.2)),
    var(--surface);
  border: 1px solid rgba(255, 150, 170, 0.35);
  overflow: hidden;
}
.team-banner .mascot {
  height: 96px;
  width: auto;
  object-fit: contain;
  flex-shrink: 0;
  filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.12));
}
.team-copy { flex: 1; min-width: 0; text-align: center; }
.team-name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #c41d7f;
  line-height: 1.3;
}
.team-sub { margin-top: 2px; color: var(--text-secondary); font-size: 13px; }
.project-chip {
  margin: 8px auto 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(242, 106, 87, 0.1);
  border: 1px solid rgba(242, 106, 87, 0.22);
  color: var(--text-primary);
  font-size: 12px;
  line-height: 1.4;
}
.project-chip-label {
  color: #c85a43;
  font-weight: 600;
  flex-shrink: 0;
}
.project-chip-name {
  font-weight: 700;
  font-size: 13px;
}
.project-chip-addr {
  color: var(--text-secondary);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mood-legend {
  margin-top: 8px;
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-secondary);
}
.mood-legend span { display: inline-flex; align-items: center; gap: 4px; }
.mood-legend img { width: 28px; height: 28px; object-fit: contain; }
.metrics { display: flex; }
.metrics-flash .metric-card {
  animation: dash-pulse 0.65s ease;
}
@keyframes dash-pulse {
  0% { transform: translateY(0); box-shadow: none; }
  40% { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(242, 106, 87, 0.14); }
  100% { transform: translateY(0); box-shadow: none; }
}
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 14px 16px;
  border-top: 3px solid #f26a57;
}
.label-with-mood { display: inline-flex; align-items: center; gap: 4px; }
.mood-mini { width: 22px; height: 22px; object-fit: contain; }
.metric-card.clickable {
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.15s;
}
.metric-card.clickable:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.metric-card.t-danger { border-top-color: #ff4d4f; }
.metric-card.t-warning { border-top-color: #fa8c16; }
.metric-card.t-success { border-top-color: #f26a57; }
.metric-label {
  color: var(--text-secondary);
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.link-hint { color: #c85a43; font-size: 12px; opacity: 0.85; }
.metric-value { font-size: 28px; font-weight: 700; line-height: 1.3; }
.unit { font-size: 14px; margin-left: 4px; font-weight: 400; }
.metric-trend { font-size: 12px; color: var(--text-secondary); }
.panel {
  background: var(--surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  height: 100%;
}
.panel-title { font-weight: 600; margin-bottom: 10px; }
.presentation-tag {
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
  padding: 1px 7px;
  border: 1px solid color-mix(in srgb, var(--text-secondary) 34%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface-muted) 82%, transparent);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 400;
  line-height: 18px;
  vertical-align: middle;
}
.sub-tip { margin-left: 8px; font-size: 12px; color: var(--text-secondary); font-weight: 400; }
.video-carousel { height: 360px; }
.carousel-item { height: 320px; padding: 0 4px; }
.carousel-item :deep(.video-player) { height: 260px; }
.stream-wrap { height: 260px; }
.cover-wrap {
  position: relative;
  height: 260px;
  border-radius: 6px;
  overflow: hidden;
  background: #4e2c27;
  cursor: pointer;
}
.cover-wrap img { width: 100%; height: 100%; object-fit: cover; display: block; }
.cover-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffd7bc;
}
.cover-badge {
  position: absolute;
  left: 10px;
  top: 10px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}
.video-caption {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 13px;
}
.video-caption .time { margin-left: auto; color: var(--text-secondary); font-size: 12px; }
.charts-panel { max-height: 420px; overflow: auto; }
.chart-box { height: 160px; }
.sub-title { font-size: 13px; font-weight: 600; margin: 8px 0; }
.rank-item, .top-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  margin-bottom: 6px;
}
.rank-no {
  width: 18px; height: 18px; border-radius: 50%;
  background: #f26a57; color: #fff; text-align: center; line-height: 18px; font-size: 11px;
}
.rank-name { width: 72px; }
.top-item { justify-content: space-between; }
.quick-bar {
  background: var(--surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px 16px;
}
.warm-ghost-btn {
  color: #c85a43 !important;
}
.ai-demo-actions {
  margin-top: 16px;
  text-align: right;
}
</style>
