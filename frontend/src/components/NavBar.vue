<template>
  <nav class="navbar navbar-toggleable-md fixed-top navbar-transparent landing-navbar">
    <div class="container">
      <div class="navbar-translate">
        <button
          class="navbar-toggler navbar-toggler-right navbar-burger landing-burger"
          type="button"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-bar"></span>
          <span class="navbar-toggler-bar"></span>
          <span class="navbar-toggler-bar"></span>
        </button>
        <button class="navbar-brand landing-brand" type="button" @click="handleBrandClick">CloudStrategy</button>
      </div>
      <div class="navbar-collapse landing-navbar-collapse" id="navbarToggler">
        <ul class="navbar-nav ml-auto landing-nav">
          <li class="nav-item">
            <a
              class="nav-link"
              rel="tooltip"
              title="Star on GitHub"
              data-placement="bottom"
              href="https://github.com/liumingliao/CloudStrategy"
              target="_blank"
              style="display:inline-flex;align-items:center;gap:6px;"
            >
              <svg height="18" width="18" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
              </svg>
            </a>
          </li>
          <li class="nav-item">
            <!-- <button class="nav-link landing-nav-btn fog-toggle" type="button" :aria-pressed="fogEnabled" @click="toggleFog">
              {{ fogEnabled ? t('home.nav.fogOn') : t('home.nav.fogOff') }}
            </button> -->
          </li>
          <li class="nav-item landing-lang-item">
            <a-select v-model:value="locale" class="lang-select-nav" size="small" :aria-label="t('app.language.label')">
              <a-select-option value="zh-CN">{{ t('app.language.zh') }}</a-select-option>
              <a-select-option value="ja-JP">{{ t('app.language.ja') }}</a-select-option>
              <a-select-option value="en-US">{{ t('app.language.en') }}</a-select-option>
            </a-select>
          </li>
          <li class="nav-item">
            <button type="button" class="btn btn-danger btn-round landing-cta" @click="handleCtaClick">
              {{ t('home.nav.cta') }}
            </button>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const emit = defineEmits<{
  (e: 'brand-click'): void
  (e: 'cta-click'): void
}>()

const handleBrandClick = () => {
  emit('brand-click')
}

const handleCtaClick = () => {
  emit('cta-click')
}
</script>

<style scoped>
.landing-navbar {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  width: 100% !important;
  z-index: 1030 !important;
  min-height: 70px;
  padding: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  border: none !important;
  border-bottom: 1px solid transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  transition: background 0.3s;
}

.landing-navbar:not(.navbar-transparent) {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border-color: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

.landing-navbar.navbar-transparent {
  padding-top: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
}

.landing-navbar *,
.landing-navbar::before,
.landing-navbar::after {
  box-sizing: border-box;
}

.landing-navbar .container {
  width: 100% !important;
  max-width: 100vw !important;
  min-height: 70px;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  padding-left: 20px;
  padding-right: 20px;
  box-sizing: border-box !important;
}

.landing-navbar .navbar-translate {
  display: flex !important;
  align-items: center !important;
  min-height: 70px;
  flex: 0 0 auto;
}

.landing-navbar .navbar-brand {
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1 !important;
}

.landing-burger {
  display: none !important;
}

.landing-brand {
  background: transparent !important;
  border: 0;
  color: #f4f8fc !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase;
  font-size: 13px !important;
  cursor: pointer;
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.landing-navbar-collapse {
  display: flex !important;
  justify-content: flex-end;
  align-items: center;
  flex: 1;
  position: static !important;
  transform: none !important;
  width: auto !important;
  height: auto !important;
  background: transparent !important;
  border: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
}

.landing-navbar-collapse::before,
.landing-navbar-collapse::after {
  display: none !important;
  content: none !important;
  background: transparent !important;
}

.landing-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 0 auto !important;
  padding: 0;
  list-style: none;
}

.landing-nav .nav-item {
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
}

.landing-nav .nav-item .nav-link {
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1 !important;
  opacity: 1 !important;
}

.landing-nav-btn {
  border: 1.2px solid rgba(236, 243, 250, 0.24);
  background: rgba(12, 23, 32, 0.56);
  color: #ecf3fa;
  border-radius: 999px;
  padding: 0 12px;
  min-height: 34px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  text-transform: uppercase;
}

.fog-toggle[aria-pressed='true'] {
  border-color: rgba(215, 110, 66, 0.55);
  background: rgba(215, 110, 66, 0.2);
  color: #ffe3d6;
}

.landing-lang-item {
  display: flex;
  align-items: center;
}

.lang-select-nav {
  width: 110px;
}

.lang-select-nav :deep(.ant-select-selector) {
  height: 34px !important;
  padding: 0 12px !important;
  border: 1.2px solid rgba(236, 243, 250, 0.24) !important;
  background: rgba(12, 23, 32, 0.56) !important;
  border-radius: 999px !important;
  display: flex !important;
  align-items: center !important;
}

.lang-select-nav :deep(.ant-select-selection-item) {
  line-height: 32px !important;
  font-size: 12px !important;
}

.lang-select-nav :deep(.ant-select-selection-item),
.lang-select-nav :deep(.ant-select-arrow) {
  color: #ecf3fa !important;
}

.landing-cta {
  min-height: 32px;
  padding: 0 14px !important;
  font-size: 12px !important;
  border: none !important;
  letter-spacing: 0.06em;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  margin: 0 !important;
}

.landing-navbar .btn {
  margin: 0 !important;
}

@media (max-width: 991px) {
  .landing-navbar {
    min-height: 64px;
  }

  .landing-navbar .container {
    padding-left: 14px;
    padding-right: 14px;
    min-height: 64px;
  }

  .landing-navbar .navbar-translate {
    min-height: 64px;
  }

  .lang-select-nav {
    width: 92px;
  }

  .landing-cta {
    min-height: 34px;
    padding: 0 10px !important;
  }

  .landing-nav {
    gap: 6px;
  }
}

@media (max-width: 520px) {
  .landing-navbar .container {
    padding-left: 8px;
    padding-right: 8px;
  }

  .landing-brand {
    font-size: 10px !important;
    letter-spacing: 0.05em !important;
    max-width: 70px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .landing-nav {
    gap: 3px !important;
  }

  .lang-select-nav {
    width: 68px !important;
  }

  .lang-select-nav :deep(.ant-select-selector) {
    padding: 0 4px !important;
  }

  .landing-cta {
    padding: 0 8px !important;
    font-size: 10px !important;
    min-height: 30px !important;
    margin-right: 0 !important;
  }
}

@media (max-width: 400px) {
  .landing-nav .nav-item:first-child {
    display: none !important;
  }

  .lang-select-nav {
    width: 62px !important;
  }
}
</style>
