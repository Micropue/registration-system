<template>
  <div class="bento-page">
    <div ref="container" class="bento-container">
      <!-- Hero Card -->
      <div class="bento-card hero-card">
        <div class="hero-avatar">
          <span>M</span>
        </div>
        <h1 class="hero-name">MICROPUE</h1>
        <p class="hero-tagline">全栈开发者 · 构建优雅的数字化体验</p>
        <div class="hero-divider"></div>
        <p class="hero-desc">专注于前后端全栈开发，热爱打造高性能、易用的 Web 应用</p>
      </div>

      <!-- Tech Stack Cards -->
      <div class="bento-grid">
        <div class="bento-card stack-card">
          <div class="card-icon frontend-icon">
            <span>FE</span>
          </div>
          <h3 class="card-title">前端</h3>
          <div class="card-tags">
            <span class="tag">Vue 3</span>
            <span class="tag">Vite</span>
            <span class="tag">TypeScript</span>
            <span class="tag">Vuetify 4</span>
            <span class="tag">Pinia</span>
            <span class="tag">Vue Router</span>
            <span class="tag">GSAP</span>
            <span class="tag">PWA</span>
          </div>
        </div>

        <div class="bento-card stack-card">
          <div class="card-icon backend-icon">
            <span>BE</span>
          </div>
          <h3 class="card-title">后端</h3>
          <div class="card-tags">
            <span class="tag">Python</span>
            <span class="tag">FastAPI</span>
            <span class="tag">MySQL 8.0</span>
            <span class="tag">WebSocket</span>
          </div>
        </div>

        <div class="bento-card stack-card">
          <div class="card-icon deploy-icon">
            <span>OP</span>
          </div>
          <h3 class="card-title">部署运维</h3>
          <div class="card-tags">
            <span class="tag">Docker</span>
            <span class="tag">Docker Compose</span>
            <span class="tag">Nginx</span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <p class="bento-footer">Built with love &amp; GSAP</p>
    </div>
  </div>
</template>

<style scoped>
/* ========== Bento Design System ========== */
.bento-page {
  min-height: calc(100vh - 64px);
  background: #FFF5E6;
  display: flex;
  justify-content: center;
  padding: 48px 24px 64px;
}

.bento-container {
  width: 100%;
  max-width: 720px;
}

/* ========== Cards ========== */
.bento-card {
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}

.bento-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

/* ========== Hero Card ========== */
.hero-card {
  text-align: center;
  padding: 48px 32px 40px;
  margin-bottom: 24px;
}

.hero-avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: linear-gradient(135deg, #FAD4C0 0%, #E8A87C 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  box-shadow: 0 8px 24px rgba(250, 212, 192, 0.4);
}

.hero-avatar span {
  font-family: 'Inter', sans-serif;
  font-size: 36px;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: -0.5px;
}

.hero-name {
  font-family: 'Inter', sans-serif;
  font-size: 32px;
  font-weight: 800;
  color: #111827;
  margin: 0 0 8px;
  letter-spacing: -1px;
}

.hero-tagline {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  margin: 0 0 20px;
}

.hero-divider {
  width: 48px;
  height: 3px;
  background: #FAD4C0;
  border-radius: 2px;
  margin: 0 auto 20px;
}

.hero-desc {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: #9CA3AF;
  margin: 0;
  line-height: 1.6;
}

/* ========== Bento Grid ========== */
.bento-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  margin-bottom: 32px;
}

@media (min-width: 600px) {
  .bento-grid {
    grid-template-columns: 1fr 1fr;
  }
}

/* ========== Stack Cards ========== */
.stack-card {
  padding: 24px;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.card-icon span {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
}

.frontend-icon {
  background: rgba(250, 212, 192, 0.3);
  color: #D4845A;
}

.backend-icon {
  background: rgba(128, 161, 193, 0.25);
  color: #5B8BA8;
}

.deploy-icon {
  background: rgba(22, 163, 74, 0.15);
  color: #16A34A;
}

.card-title {
  font-family: 'Inter', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 16px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: #6B7280;
  background: #F9FAFB;
  border: 1px solid #F3F4F6;
  transition: all 0.2s ease;
}

.tag:hover {
  color: #111827;
  border-color: #E5E7EB;
  background: #F3F4F6;
}

/* ========== Footer ========== */
.bento-footer {
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #D1D5DB;
  margin: 0;
}
</style>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import gsap from 'gsap'

const container = ref<HTMLElement | null>(null)
let ctx: gsap.Context | null = null

onMounted(async () => {
  await nextTick()
  if (!container.value) return

  ctx = gsap.context(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } })

    gsap.set('.hero-card', { y: 40, opacity: 0 })
    gsap.set('.stack-card', { y: 30, opacity: 0 })
    gsap.set('.bento-footer', { opacity: 0 })

    tl.to('.hero-card', { y: 0, opacity: 1, duration: 0.7 })
    tl.to('.stack-card', { y: 0, opacity: 1, duration: 0.5, stagger: 0.12 }, '-=0.3')
    tl.to('.bento-footer', { opacity: 1, duration: 0.5 }, '-=0.2')
  }, container.value)
})

onUnmounted(() => {
  ctx?.revert()
})
</script>
