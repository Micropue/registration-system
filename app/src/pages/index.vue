<template>
  <div class="home">
    <h1 class="home-h1">多啦A梦校园跑综合服务平台</h1>
    <div class="cards">
      <v-card border rounded="lg" class="card">
        <v-icon icon="mdi-speedometer" size="50" color="blue"></v-icon>
        <p>高速响应</p>
      </v-card>
      <v-card border rounded="lg" class="card">
        <v-icon icon="mdi-chart-timeline-variant-shimmer" size="50" color="blue"></v-icon>
        <p>极简设计</p>
      </v-card>
    </div>
    <p class="tip">系统由MICROPUE提供服务</p>
  </div>
</template>
<script setup lang="ts">
import { gsap } from 'gsap'
import { onMounted } from 'vue'
import SplitText from 'gsap/SplitText'
onMounted(() => {
  gsap.registerPlugin(SplitText)
  const chars = SplitText.create(".home-h1", { type: 'chars' })
  const tl = gsap.timeline()
  tl.from(chars.chars, {
    y: 10,
    stagger: 0.05,
    opacity: 0,
  }).from(".card", {
    y: 10,
    scale: 0,
    stagger: 0.3,
  }).from(".tip", {
    opacity: 0
  })
})
</script>
<style lang="scss" scoped>
.home {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  h1 {
    font-size: 3em;
  }

  .cards {
    display: flex;
    align-items: center;

    .v-card {
      margin: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: none;
      padding: 10px;
      color: #2196F3;
      font-weight: 900;
      font-size: 1.1em;

      p {
        margin-left: 10px;
      }
    }
  }
}
</style>