import { ref } from 'vue'

const STORAGE_KEY = 'znt_color_theme'
const saved = localStorage.getItem(STORAGE_KEY)
export const colorTheme = ref(saved === 'dark' ? 'dark' : 'light')

function applyTheme(value) {
  document.documentElement.dataset.theme = value
  document.documentElement.style.colorScheme = value
}

export function setColorTheme(value) {
  colorTheme.value = value === 'dark' ? 'dark' : 'light'
  localStorage.setItem(STORAGE_KEY, colorTheme.value)
  applyTheme(colorTheme.value)
}

export function toggleColorTheme() {
  setColorTheme(colorTheme.value === 'dark' ? 'light' : 'dark')
}

applyTheme(colorTheme.value)
