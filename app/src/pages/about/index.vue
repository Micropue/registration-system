<template>
  <div class="about-page">
    <!-- 背景光球 -->
    <div class="bg-orbs">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <div ref="container" class="about-body">
      <h1 ref="titleEl" class="title"></h1>
      <p class="subtitle">全栈开发者 · 构建优雅的数字化体验</p>
      <p class="desc">专注于前后端全栈开发，热爱打造高性能、易用的 Web 应用</p>

      <div class="stacks">
        <div class="stack-card">
          <div class="stack-head">
            <i class="mdi mdi-monitor-dashboard stack-head-icon" style="color:#40C894"></i>
            <h3>前端</h3>
          </div>
          <div class="stack-items">
            <span><i class="mdi mdi-vuejs"></i>Vue 3</span>
            <span><i class="mdi mdi-lightning-bolt"></i>Vite</span>
            <span><i class="mdi mdi-language-typescript"></i>TypeScript</span>
            <span><i class="mdi mdi-vuetify"></i>Vuetify 4</span>
            <span><i class="mdi mdi-fruit-pineapple"></i>Pinia</span>
            <span><i class="mdi mdi-routes"></i>Vue Router</span>
            <span><i class="mdi mdi-animation-play"></i>GSAP</span>
            <span><i class="mdi mdi-cellphone-arrow-down"></i>PWA</span>
          </div>
        </div>
        <div class="stack-card">
          <div class="stack-head">
            <i class="mdi mdi-server stack-head-icon" style="color:#60B0F0"></i>
            <h3>后端</h3>
          </div>
          <div class="stack-items">
            <span><i class="mdi mdi-language-python"></i>Python</span>
            <span><i class="mdi mdi-api"></i>FastAPI</span>
            <span><i class="mdi mdi-database"></i>MySQL 8.0</span>
            <span><i class="mdi mdi-connection"></i>WebSocket</span>
          </div>
        </div>
        <div class="stack-card">
          <div class="stack-head">
            <i class="mdi mdi-docker stack-head-icon" style="color:#CC5D46"></i>
            <h3>部署运维</h3>
          </div>
          <div class="stack-items">
            <span><i class="mdi mdi-docker"></i>Docker</span>
            <span><i class="mdi mdi-layers-triple"></i>Docker Compose</span>
            <span><i class="mdi mdi-server-network"></i>Nginx</span>
          </div>
        </div>
      </div>

      <p class="service-text">micropue.com.cn提供技术服务</p>
    </div>
  </div>
</template>

<style scoped>
.about-page {
  min-height: calc(100vh - 64px);
  background: #090909;
  position: relative;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  padding: 64px 32px 80px;
  overflow: hidden;
  box-sizing: border-box;
}

/* === 背景光球 === */
.bg-orbs {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 0; height: 0;
  animation: orb-rotate 25s ease-in-out infinite;
  z-index: 0;
}
@keyframes orb-rotate {
  0%, 100% { transform: translate(-50%, -50%) rotate(0deg); }
  50% { transform: translate(-50%, -50%) rotate(180deg) scale(0.6); }
}
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.45;
}
.orb-1 {
  width: 280px; height: 280px;
  background: #40C894;
  transform: translate(-140px, -70px);
  animation: orb1 12s ease-in-out infinite;
}
@keyframes orb1 { 50% { transform: translate(60px, -140px) scale(1.3); } }
.orb-2 {
  width: 240px; height: 240px;
  background: #BB3DA4;
  transform: translate(80px, -100px);
  animation: orb2 14s ease-in-out infinite;
}
@keyframes orb2 { 50% { transform: translate(-100px, 80px) scale(0.8); } }
.orb-3 {
  width: 220px; height: 220px;
  background: #CC5D46;
  transform: translate(-60px, 120px);
  animation: orb3 16s ease-in-out infinite;
}
@keyframes orb3 { 50% { transform: translate(120px, -40px) scale(1.1); } }

/* === 内容 === */
.about-body {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 680px;
}

/* === 标题 === */
.title {
  font-family: 'Inter', system-ui, sans-serif;
  font-size: clamp(42px, 10vw, 76px);
  font-weight: 900;
  font-style: italic;
  margin: 0 0 12px;
  line-height: 1.05;
  letter-spacing: -2px;
  color: transparent;
  background: linear-gradient(135deg, #40C894 0%, #2196F3 40%, #BB3DA4 100%);
  -webkit-background-clip: text;
  background-clip: text;
  width: fit-content;
}
.title .char {
  display: inline-block;
  color: transparent;
}
.subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 16px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 8px;
}
.desc {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.28);
  margin: 0 0 40px;
  line-height: 1.6;
}

/* === 技术栈 === */
.stacks {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin-bottom: 32px;
}
@media (min-width: 600px) {
  .stacks { grid-template-columns: 1fr 1fr; }
}
.stack-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 16px;
  padding: 24px;
  transition: background .3s, border-color .3s, transform .3s;
}
.stack-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.14);
  transform: translateY(-2px);
}
.stack-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.stack-head-icon { font-size: 22px; }
.stack-head h3 {
  font-family: 'Inter', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
}
.stack-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.stack-items span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all .2s;
}
.stack-items span i { font-size: 14px; opacity: 0.6; }
.stack-items span:hover {
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.14);
}
.stack-items span:hover i { opacity: 1; }

/* === 底部 === */
.service-text {
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.2);
  margin: 0;
}
</style>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import gsap from 'gsap'

const container = ref<HTMLElement | null>(null)
const titleEl = ref<HTMLElement | null>(null)
let ctx: gsap.Context | null = null

onMounted(async () => {
  await nextTick()
  if (!container.value) return

  if (titleEl.value) {
    titleEl.value.innerHTML = 'MICROPUE'
      .split('')
      .map(c => `<span class="char">${c}</span>`)
      .join('')
  }

  ctx = gsap.context(() => {
    gsap.set('.char', { x: 60, opacity: 0 })
    gsap.set('.subtitle', { y: 16, opacity: 0 })
    gsap.set('.desc', { y: 12, opacity: 0 })
    gsap.set('.stack-card', { y: 30, opacity: 0 })
    gsap.set('.service-text', { opacity: 0 })

    const tl = gsap.timeline({ defaults: { ease: 'power4.out' } })

    tl.to('.char', {
      x: 0,
      opacity: 1,
      duration: 0.65,
      stagger: { each: 0.04, from: 'start' },
      ease: 'back.out(2)',
    }, 0.2)

    tl.to('.subtitle', { y: 0, opacity: 1, duration: 0.5 }, '-=0.35')
    tl.to('.desc', { y: 0, opacity: 1, duration: 0.5 }, '-=0.3')
    tl.to('.stack-card', {
      y: 0, opacity: 1, duration: 0.55,
      stagger: { each: 0.14, from: 'start' },
      ease: 'power3.out',
    }, '-=0.2')
    tl.to('.service-text', { opacity: 1, duration: 0.5 }, '-=0.2')
  }, container.value)
})

onUnmounted(() => {
  ctx?.revert()
})
</script>
