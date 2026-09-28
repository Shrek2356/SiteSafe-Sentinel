/** Single palette for CSS, Ant Design and charts. Risk colors are not action colors. */
const shared = {
  'card-radius': '10px', 'product-ink': '#0b1930', 'media-bg': '#091323',
  'hero-accent': '#88c7ff', 'hero-text': '#f0f6ff', 'hero-muted': '#abc0dc',
}
export const palettes = {
  light: {
    ...shared,
    bg: '#f3f2ee', 'bg-2': '#eae9e4', surface: '#fffefa', 'surface-2': '#f4f3ef',
    'surface-muted': '#e9e8e3', 'border-color': '#d4d2ca',
    'text-primary': '#252522', 'text-secondary': '#53534f', 'text-muted': '#65655f',
    primary: '#30302d', 'primary-strong': '#141413', 'primary-soft': '#e7e6e0',
    'on-primary': '#ffffff', 'on-danger': '#ffffff', link: '#363632', danger: '#c73749', warning: '#9a6100',
    caution: '#806400', success: '#187b5b', info: '#555550',
    'sider-bg': '#faf9f5', 'sider-text': '#53534f', 'sider-muted': '#65655f',
    'sider-active': '#e7e6e0', 'sider-trigger': '#faf9f5', 'sider-trigger-hover': '#eeede7',
    'shadow-card': '0 2px 4px #22222203, 0 8px 28px #22222204',
    'shadow-float': '0 16px 48px #22222216',
    'chart-1': '#30302d', 'chart-2': '#60605b', 'chart-3': '#86867e',
    'chart-4': '#a6a69d', 'chart-5': '#c4c4ba',
    'product-ink': '#eeede7', 'hero-text': '#252522', 'hero-muted': '#53534f', 'hero-accent': '#30302d',
  },
  dark: {
    ...shared,
    bg: '#080f20', 'bg-2': '#0c1830', surface: '#101f38', 'surface-2': '#162942',
    'surface-muted': '#1c3350', 'border-color': '#2e4668',
    'text-primary': '#e9f1ff', 'text-secondary': '#b8c9e2', 'text-muted': '#a4b9d6',
    primary: '#82bdff', 'primary-strong': '#b0d7ff', 'primary-soft': '#203c61',
    'on-primary': '#09162d', 'on-danger': '#3f0f18', link: '#91c6ff', danger: '#ff8391', warning: '#f5b86b',
    caution: '#e8cf76', success: '#70d6ad', info: '#85bcef',
    'sider-bg': '#0b162a', 'sider-text': '#b8c9e2', 'sider-muted': '#a4b9d6',
    'sider-active': '#203c61', 'sider-trigger': '#0b162a', 'sider-trigger-hover': '#162942',
    'shadow-card': '0 2px 4px #00000008, 0 8px 28px #00000008',
    'shadow-float': '0 16px 48px #00000035',
    'chart-1': '#82bdff', 'chart-2': '#b4d6ff', 'chart-3': '#91a6f5',
    'chart-4': '#85b6cf', 'chart-5': '#aebcd3',
  },
}

export function paletteFor(mode) { return palettes[mode === 'dark' ? 'dark' : 'light'] }
export function antTokens(mode) {
  const p = paletteFor(mode)
  return {
    colorPrimary: p.primary, colorPrimaryHover: p['primary-strong'], colorPrimaryActive: p['primary-strong'],
    colorPrimaryBg: p['primary-soft'], colorPrimaryBgHover: p['primary-soft'], colorPrimaryText: p.link,
    colorLink: p.link, colorLinkHover: p['primary-strong'], colorLinkActive: p['primary-strong'],
    colorSuccess: p.success, colorWarning: p.warning, colorError: p.danger, colorInfo: p.info,
    colorBgBase: p.surface, colorBgContainer: p.surface, colorBgElevated: p.surface,
    colorBgLayout: p.bg, colorFillAlter: p['surface-2'], colorBorder: p['border-color'], colorBorderSecondary: p['border-color'],
    colorText: p['text-primary'], colorTextBase: p['text-primary'], colorTextSecondary: p['text-secondary'],
    colorTextTertiary: p['text-muted'], colorTextQuaternary: p['text-muted'],
    colorTextLightSolid: '#ffffff', colorBgSpotlight: '#202020', borderRadius: 6, borderRadiusLG: 10,
    fontFamily: '"Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
    fontSize: 14, controlHeight: 36, boxShadowSecondary: p['shadow-float'],
  }
}

export function chartTheme(mode) {
  const p = paletteFor(mode)
  return {
    text: p['text-secondary'], grid: p['border-color'], primary: p.primary,
    danger: p.danger, warning: p.warning, caution: p.caution,
    colors: [1, 2, 3, 4, 5].map(i => p[`chart-${i}`]),
    tooltip: { backgroundColor: p.surface, borderColor: p['border-color'], textStyle: { color: p['text-primary'], fontSize: 12 }, extraCssText: 'border-radius:10px;box-shadow:' + p['shadow-float'] },
  }
}
