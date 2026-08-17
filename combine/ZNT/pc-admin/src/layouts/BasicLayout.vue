<template>
  <a-layout class="basic-layout">
    <!-- 侧边栏 -->
    <a-layout-sider v-model:collapsed="collapsed" collapsible theme="dark" width="240">
      <div class="logo">
        <span v-if="!collapsed" class="logo-full">
          <span class="logo-title">工地安全智能检测系统</span>
          <span class="logo-team">嘉然今天也在守护工地</span>
        </span>
        <span v-else>安全</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="onMenuClick"
      >
        <a-menu-item v-for="item in visibleMenus" :key="item.path">
          <component :is="iconMap[item.meta.icon]" />
          <span>{{ item.meta.title }}</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <!-- 顶栏 -->
      <a-layout-header class="header">
        <div class="header-left">
          <a-select
            v-model:value="projectId"
            style="width: 260px"
            placeholder="切换项目"
            @change="onProjectChange"
          >
            <a-select-option v-for="p in projects" :key="p.id" :value="p.id">
              {{ p.name }}
            </a-select-option>
          </a-select>
        </div>
        <div class="header-right">
          <a-tooltip :title="colorTheme === 'dark' ? '切换明亮模式' : '切换暗色模式'">
            <a-button class="theme-toggle" shape="circle" @click="toggleColorTheme">
              <BulbOutlined v-if="colorTheme === 'dark'" />
              <span v-else aria-hidden="true">☾</span>
            </a-button>
          </a-tooltip>
          <a-tag color="orange">{{ ROLE_LABELS[userStore.role] || userStore.role }}</a-tag>
          <span class="username">{{ userStore.displayName }}</span>
          <a-button type="link" @click="onLogout">退出</a-button>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="content">
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
} from '@ant-design/icons-vue'
import { getMenuRoutes } from '@/router'
import { useUserStore } from '@/stores/user'
import { ROLE_LABELS } from '@/utils/permission'
import { fetchProjects } from '@/api/resource'
import { message } from 'ant-design-vue'
import { colorTheme, toggleColorTheme } from '@/utils/theme'
import { startBusinessSocket, stopBusinessSocket } from '@/utils/businessSocket'

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
  await userStore.setProject(id)
  message.success('已切换项目')
}

function onLogout() {
  userStore.logout()
  router.push('/login')
}

onMounted(async () => {
  startBusinessSocket()
  const res = await fetchProjects()
  projects.value = res.data
  const savedProjectExists = res.data.some((item) => item.id === userStore.project?.id)
  if (!savedProjectExists && res.data[0]) {
    await userStore.setProject(res.data[0].id)
    projectId.value = res.data[0].id
  } else if (savedProjectExists) {
    projectId.value = userStore.project.id
  }
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
</style>
