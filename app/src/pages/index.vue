<template>
  <div class="home">
    <section class="section-1">
      <div class="logo">
        <h1 class="logo-title">多啦A梦校园跑</h1>
        <p class="major">8年专业校园跑</p>
      </div>
      <img class="doraemon" src="../assets/doraemon.jpeg" alt="" />
      <div class="continue-scroll">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24">
          <!-- Icon from Material Design Icons by Pictogrammers - https://github.com/Templarian/MaterialDesign/blob/master/LICENSE -->
          <path fill="currentColor" d="M11 4h2v12l5.5-5.5l1.42 1.42L12 19.84l-7.92-7.92L5.5 10.5L11 16z" />
        </svg>
        <p>继续向下滚动</p>
      </div>
    </section>
  </div>
</template>
<style lang="scss" scoped>
.home {
  position: fixed;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  top: 0;
  left: 0;
  word-wrap: break-word;
  overflow: hidden;

  section {
    width: 100%;
    height: 100%;
  }

  .section-1 {
    font-size: 3em;
    display: flex;
    align-items: center;
    padding: 4em 4em;

    .logo {
      display: flex;
      flex-direction: column;
      align-items: start;

      h1 {
        margin: 0;
        margin-bottom: 0;
      }

      p.major {
        margin: 0;
        font-size: 0.5em;
        margin-top: 0;
        margin-left: 10px;
        color: gray;
      }
    }
  }

  .doraemon {
    width: 13em;
    position: absolute;
    bottom: 0;
    top: 0;
    margin: auto;
    right: 4em;
  }

  .continue-scroll {
    position: absolute;
    bottom: 0;
    font-size: 1rem;
    color: gray;
    display: flex;
    justify-content: center;
    align-items: center;
    left: 0;
    flex-direction: column;
    right: 0;
    margin: auto;
    width: fit-content;
    opacity: 0;
    animation: continue-loop 2s ease-in-out infinite;

    @keyframes continue-loop {
      0% {
        opacity: 0;
        transform: translateY(-10px);
      }

      30% {
        opacity: 1;
      }

      50% {
        opacity: 1;
        transform: translateY(10px);
      }

      80% {
        opacity: 0;
      }

      100% {
        transform: translateY(10px);
      }
    }

    svg {
      fill: gray;
      width: 20px;
      height: 20px;
    }
  }
}
</style>
<script lang="ts" setup>
import { gsap } from "gsap";
import SplitText from "gsap/SplitText";
import { onMounted } from "vue";
gsap.registerPlugin(SplitText);
onMounted(() => {
  const split = SplitText.create(".logo .logo-title", {
    type: "chars",
  });
  const tl = gsap.timeline();
  // 为每个字符应用随机动画效果
  tl.from(split.chars, {
    duration: 1,
    opacity: 0,
    scale: () => gsap.utils.random(0.5, 1.5), // 随机缩放
    rotation: () => gsap.utils.random(-90, 90), // 随机旋转
    x: () => gsap.utils.random(-100, 100), // 随机X轴偏移
    y: () => gsap.utils.random(-100, 100), // 随机Y轴偏移
    stagger: 0.01, // 依次进入
    ease: "back",
  })
    .from(".major", {
      duration: 1,
      delay: 0.5,
      opacity: 0,
      y: 20,
      ease: "power2.out",
    })
    .from(".doraemon", {
      x: 200,
      opacity: 0,
      ease: "bounce",
      duration: 1,
    });
});
</script>
