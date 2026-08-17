<template>
  <!-- 全局暖色主题：覆盖 Ant Design 默认蓝色主色/链接色/信息色 -->
  <a-config-provider :theme="activeTheme">
    <router-view />
  </a-config-provider>
</template>

<script setup>
/**
 * 根组件
 * 仅作为路由容器，业务页面见 views/ 目录
 * 主题色与 styles/global.css 中的 CSS 变量保持一致
 */
import { computed } from 'vue'
import { theme as antTheme } from 'ant-design-vue'
import { colorTheme } from '@/utils/theme'

const warmTokens = {
  colorPrimary: '#f26a57',
  colorInfo: '#f26a57',
  colorLink: '#c85a43',
  colorLinkHover: '#e85447',
  colorLinkActive: '#c44932',
  colorPrimaryHover: '#e85447',
  colorPrimaryActive: '#d4483a',
  colorPrimaryBorder: '#f2b29f',
  colorPrimaryBorderHover: '#f0a14d',
  controlOutline: 'rgba(242, 106, 87, 0.2)',
  colorPrimaryBg: '#fff1ea',
  colorPrimaryBgHover: '#ffe1d4',
}

const activeTheme = computed(() => ({
  algorithm: colorTheme.value === 'dark' ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm,
  token: {
    ...warmTokens,
    colorBgBase: colorTheme.value === 'dark' ? '#111820' : '#ffffff',
    colorTextBase: colorTheme.value === 'dark' ? '#edf2f5' : '#1f1f1f',
  },
}))
</script>
