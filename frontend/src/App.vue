<script setup>
import { computed, ref, watch } from 'vue'
import { darkTheme, NConfigProvider, NMessageProvider } from 'naive-ui'
import Workspace from './components/Workspace.vue'
import { createThemeOverrides } from './theme'

const STORAGE_KEY = 'chat-ui-theme'
const requested = new URLSearchParams(location.search).get('theme')
const theme = ref(
  requested === 'light' || requested === 'dark'
    ? requested
    : localStorage.getItem(STORAGE_KEY) === 'light'
      ? 'light'
      : 'dark',
)

watch(
  theme,
  (value) => {
    localStorage.setItem(STORAGE_KEY, value)
    document.documentElement.dataset.theme = value
  },
  { immediate: true },
)

const isDark = computed(() => theme.value === 'dark')
const themeOverrides = computed(() => createThemeOverrides(isDark.value))

function toggleTheme() {
  theme.value = isDark.value ? 'light' : 'dark'
}
</script>

<template>
  <n-config-provider :theme="isDark ? darkTheme : null" :theme-overrides="themeOverrides">
    <n-message-provider :max="2" placement="top-right">
      <Workspace :theme="theme" @toggle-theme="toggleTheme" />
    </n-message-provider>
  </n-config-provider>
</template>
