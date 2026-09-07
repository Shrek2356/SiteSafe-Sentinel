<template>
  <a-layout class="basic-layout">
    <a class="skip-content" href="#main-content">跳转到页面内容</a>
    <!-- 侧边栏 -->
    <a-layout-sider v-model:collapsed="collapsed" collapsible theme="dark" width="224">
      <div class="logo">
        <SafetyCertificateOutlined class="brand-symbol" />
        <span v-if="!collapsed" class="logo-full">
          <span class="logo-title">筑安智巡</span>
          <span class="logo-team">SITESAFE SENTINEL</span>
        </span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="onMenuClick"
      >
        <a-menu-item-group v-for="group in menuGroups" :key="group.title" :title="collapsed ? '' : group.title">
          <a-menu-item v-for="item in group.items" :key="item.path">
            <component :is="iconMap[item.meta.icon]" />
            <span>{{ item.meta.title }}</span>
          </a-menu-item>
        </a-menu-item-group>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <!-- 顶栏 -->
      <a-layout-header class="header">
        <div class="header-left">
          <span class="project-label">当前项目</span>
          <a-select
            v-model:value="projectId"
            style="width: 218px"
            placeholder="切换项目"
            aria-label="切换当前项目"
            @change="onProjectChange"
          >
            <a-select-option v-for="p in projects" :key="p.id" :value="p.id">
              {{ p.name }}
            </a-select-option>
          </a-select>
        </div>
        <div class="header-right">
          <ProductGuide />
          <a-radio-group class="workspace-style-switch" :value="workspaceStyle" size="small" @change="e => setWorkspaceStyle(e.target.value)">
            <a-radio-button value="professional">工作台</a-radio-button>
            <a-radio-button value="showcase">展示视图</a-radio-button>
          </a-radio-group>
          <a-tooltip :title="colorTheme === 'dark' ? '切换明亮模式' : '切换暗色模式'">
            <a-button class="theme-toggle" shape="circle" :aria-label="colorTheme === 'dark' ? '切换明亮模式' : '切换暗色模式'" @click="toggleColorTheme">
              <BulbOutlined v-if="colorTheme === 'dark'" />
              <span v-else aria-hidden="true">☾</span>
            </a-button>
          </a-tooltip>
          <a-dropdown placement="bottomRight" :trigger="['click']"><a-button class="user-menu"><UserOutlined /><span class="username">{{ userStore.displayName }}</span><DownOutlined /></a-button><template #overlay><a-menu><a-menu-item disabled>{{ ROLE_LABELS[userStore.role] || userStore.role }}</a-menu-item><a-menu-item @click="router.push('/help-center')">使用与支持</a-menu-item><a-menu-item @click="setWorkspaceStyle(workspaceStyle === 'professional' ? 'showcase' : 'professional')">{{ workspaceStyle === 'professional' ? '切换为作品展示视图' : '切换为专业工作台' }}</a-menu-item><a-menu-divider /><a-menu-item @click="onLogout">退出登录（后台任务继续）</a-menu-item></a-menu></template></a-dropdown>
        </div>
      </a-layout-header>
      <RuntimeStatus />

      <!-- 内容区 -->
      <a-layout-content id="main-content" tabindex="-1" class="content">
        <div class="page-location"><span>工作空间</span><span>/</span><strong>{{ route.meta.title }}</strong><span v-if="route.path !== '/dashboard'" class="location-summary">{{ pageFor(route.path)?.description }}</span></div>
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
/**
 * 主布局：侧栏菜单 + 顶栏项目切换 + 内容区
 * 【后续修改入口】菜单来自路由 meta，新增页面只需加路由
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DashboardOutlined,
  VideoCameraOutlined,
  FileProtectOutlined,
  BarChartOutlined,
  ExperimentOutlined,
  BookOutlined,
  ClusterOutlined,
  SafetyCertificateOutlined,
  RadarChartOutlined,
  BulbOutlined,
  TeamOutlined,
  QuestionCircleOutlined, UserOutlined, DownOutlined,
} from '@ant-design/icons-vue'
import { getMenuRoutes } from '@/router'
import { useUserStore } from '@/stores/user'
import { ROLE_LABELS } from '@/utils/permission'
import { fetchProjects } from '@/api/resource'
import { message } from 'ant-design-vue'
import { colorTheme, toggleColorTheme } from '@/utils/theme'
import { startBusinessSocket, stopBusinessSocket } from '@/utils/businessSocket'
import RuntimeStatus from '@/components/RuntimeStatus.vue'
import { workspaceStyle, setWorkspaceStyle } from '@/utils/preferences'
import ProductGuide from '@/components/ProductGuide.vue'
import { pageFor } from '@/utils/guidance'

const iconMap = {
  DashboardOutlined,
  VideoCameraOutlined,
  FileProtectOutlined,
  BarChartOutlined,
  ExperimentOutlined,
  BookOutlined,
  ClusterOutlined,
  SafetyCertificateOutlined,
  RadarChartOutlined,
  TeamOutlined,
  QuestionCircleOutlined,
}

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const collapsed = ref(false)
const selectedKeys = ref([route.path.replace(/^\//, '')])
const projects = ref([])
const projectId = ref(userStore.project?.id || '')

const visibleMenus = computed(() => {
  const role = userStore.role
  return getMenuRoutes().filter((m) => {
    const roles = m.meta?.roles
    if (!roles?.length) return true
    return roles.includes(role)
  })
})
const menuGroups = computed(() => [
  ['巡检工作台', ['dashboard','monitor','realtime-detect','task-center']],
  ['风险与闭环', ['detection-results','workorder','agent-center']],
  ['知识与复盘', ['analysis','case-library']],
  ['配置与资源', ['model-config','resource','system-settings']],
  ['使用指南', ['help-center']],
].map(([title, paths]) => ({ title, items:paths.map(path => visibleMenus.value.find(m => m.path === path)).filter(Boolean) })).filter(g => g.items.length))

watch(
  () => route.path,
  (p) => {
    selectedKeys.value = [p.replace(/^\//, '')]
  }
)

function onMenuClick({ key }) {
  router.push('/' + key)
}

async function onProjectChange(id) {
  try { await userStore.setProject(id); message.success('已切换项目') }
  catch { projectId.value = userStore.project?.id || ''; message.error('项目切换失败，已保留原项目。请检查业务连接后重试。') }
}

function onLogout() {
  userStore.logout()
  router.push('/login')
}

onMounted(async () => {
  startBusinessSocket()
  try {
  const res = await fetchProjects()
  projects.value = res.data
  const savedProjectExists = res.data.some((item) => item.id === userStore.project?.id)
  if (!savedProjectExists && res.data[0]) {
    await userStore.setProject(res.data[0].id)
    projectId.value = res.data[0].id
  } else if (savedProjectExists) {
    userStore.updateProjectMetadata(res.data.find(item => item.id === userStore.project.id))
    projectId.value = userStore.project.id
  }
  } catch { message.warning('项目列表暂未加载，可从连接诊断检查业务后台。') }
})

onBeforeUnmount(stopBusinessSocket)
</script>

<style scoped>
.basic-layout {
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
  background: transparent;
}
.basic-layout > :deep(.ant-layout) {
  height: 100vh;
  min-width: 0;
  overflow: hidden;
  background: transparent;
  display: flex;
  flex-direction: column;
}
:deep(.ant-layout-sider) {
  height: 100vh !important;
  max-height: 100vh;
  position: sticky;
  top: 0;
  overflow: hidden;
}
:deep(.ant-layout-sider-dark) {
  /* 固定视口渐变，侧栏拉长时菜单项背景色不再随滚动漂移 */
  background-color: var(--sider-bg);
  background-image: var(--sider-gradient);
  background-attachment: fixed;
  background-repeat: no-repeat;
  background-size: 100vw 100vh;
}
:deep(.ant-layout-sider-children) {
  height: calc(100vh - 48px);
  overflow-x: hidden;
  overflow-y: auto;
}
:deep(.ant-menu-dark) {
  background: transparent;
}
:deep(.ant-menu-dark .ant-menu-item) {
  background: transparent;
}
:deep(.ant-menu-dark .ant-menu-item-selected),
:deep(.ant-menu-dark .ant-menu-item-selected:hover) {
  background: var(--sider-active);
}
:deep(.ant-layout-sider-trigger) {
  background: var(--sider-trigger);
  color: #fff4ed;
  border-top: 1px solid rgba(255, 237, 227, 0.18);
}
:deep(.ant-layout-sider-trigger:hover) {
  background: var(--sider-trigger-hover);
}
.logo {
  height: auto;
  min-height: 56px;
  margin: 12px 10px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  line-height: 1.3;
  text-align: center;
  background: var(--sider-logo);
  border: 1px solid rgba(255, 240, 231, 0.16);
  border-radius: 6px;
  flex-shrink: 0;
}
.logo-full {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.logo-title { font-size: 13px; }
.logo-team {
  font-size: 11px;
  font-weight: 500;
  color: #ffd8b6;
  letter-spacing: 0.02em;
}
.header {
  background: linear-gradient(90deg, var(--surface) 0%, var(--surface-2) 100%);
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.username {
  color: var(--text-secondary);
}
.theme-toggle { display: inline-flex; align-items: center; justify-content: center; }
.content {
  margin: 16px;
  min-height: 0;
  flex: 1;
  overflow: auto;
  background: transparent;
}
.skip-content{position:fixed;left:12px;top:-100px;background:var(--surface);color:var(--text-primary);padding:12px 20px;border:2px solid var(--primary);border-radius:8px;z-index:2000}.skip-content:focus{top:12px}
.logo{border:0;background:none;justify-content:flex-start;gap:12px;margin:22px 16px 24px;padding:0;text-align:left;min-height:46px}.brand-symbol{display:grid;place-items:center;flex-shrink:0;width:40px;height:44px;border:1px solid #eed0b633;border-radius:13px;color:#eac3a8;font-size:26px;background:#ffffff07}.logo-title{font-size:21px;letter-spacing:3px;font-weight:650}.logo-team{font-size:8px;letter-spacing:1.6px;color:#96b0b8;margin-top:5px}.header{height:76px;line-height:normal;padding:0 24px;background:var(--surface);box-shadow:none;border-bottom:1px solid var(--border-color)}.header-left{display:flex;flex-direction:column;gap:6px}.project-label{font-size:10px;color:var(--text-muted);letter-spacing:1.3px}.header-right{gap:14px}.header-left :deep(.ant-select-selector){border:0!important;box-shadow:none!important;background:transparent!important;padding-left:0!important;font-weight:600}.user-menu{border:0;background:transparent;font-size:12px}.username{max-width:90px;overflow:hidden;text-overflow:ellipsis;display:inline-block;vertical-align:middle}.page-location{display:flex;align-items:center;gap:10px;font-size:11px;color:var(--text-muted);margin:1px 0 18px;min-height:18px}.page-location strong{font-weight:500;color:var(--text-secondary)}.location-summary{margin-left:auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:65%;font-size:11px}.content{margin:20px 24px;scrollbar-gutter:stable}:deep(.ant-menu-item){height:42px!important;line-height:42px!important;margin-block:4px!important;border-radius:9px!important}:deep(.ant-menu-item-group-title){padding-top:18px!important}:deep(.ant-layout-sider-trigger){border-top:1px solid #ffffff0d;color:#9cb0bb}:deep(.ant-menu-dark .ant-menu-item-selected){color:#fff4e9}
@media(max-width:1360px){.workspace-style-switch{display:none}.header-right{gap:9px}.header{padding:0 18px}.content{margin:18px}}@media(max-width:1150px){.username{display:none}.location-summary{display:none}}
</style>
