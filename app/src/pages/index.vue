<template>
  <div class="home">
    <div class="content-wrapper">
      <!-- ========== 第一屏：Hero ========== -->
      <section class="section-1">
        <!-- Hero 卡片：哆啦A梦作为背景 -->
        <div class="hero-card" :style="{ backgroundImage: `url(${doraemonUrl})` }">
          <div class="hero-overlay"></div>

          <div class="hero-inner">
            <span class="hero-mark">✦</span>
            <h1 class="logo-title">哆啦A梦校园跑</h1>
            <p class="hero-sub">
              8 年专业校园跑服务，安全稳定、千人信赖<br />
              为你的校园生活解锁高效与自由
            </p>
            <v-btn class="btn-pill hero-cta" to="/login">开始使用</v-btn>
          </div>
        </div>

        <div class="continue-scroll">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24">
            <path fill="currentColor" d="M11 4h2v12l5.5-5.5l1.42 1.42L12 19.84l-7.92-7.92L5.5 10.5L11 16z" />
          </svg>
          <p>向下滚动</p>
        </div>
      </section>

      <!-- ========== 第二屏：特性 ========== -->
      <section id="features" class="section-2">
        <div class="intro-row">
          <div class="intro-left">
            <p class="eyebrow">关于</p>
            <h2 class="intro-title">为什么选择我们</h2>
          </div>
          <p class="intro-right">
            一款深耕校园场景 8 年的跑步代跑服务，帮助同学们在保证安全的前提下，
            轻松完成学校体育跑步任务，把时间还给真正重要的事。
          </p>
        </div>

        <div class="feature-grid">
          <article v-for="(feature, index) in features" :key="index" class="feature-card"
            :class="{ 'is-light': index % 3 === 0 }">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" width="28" height="28">
                <path :d="feature.path" fill="currentColor" />
              </svg>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.desc }}</p>
          </article>
        </div>
      </section>

      <!-- ========== 第三屏：联系我们 ========== -->
      <section id="contact" class="section-3">
        <p class="eyebrow center">CONTACT</p>
        <h2 class="contact-title">联系我们</h2>

        <div class="contact-grid">
          <div class="contact-item">
            <p class="contact-label">技术支持邮箱</p>
            <p class="contact-value">infohubjunction@micropue.com.cn</p>
          </div>
          <div class="contact-item">
            <p class="contact-label">官方微信客服</p>
            <p class="contact-value">DoraemonRun</p>
          </div>
          <div class="contact-item">
            <p class="contact-label">工作时间</p>
            <p class="contact-value">周一至周五 09:00–18:00</p>
          </div>
        </div>

        <v-btn class="btn-pill dark large" @click="go('weixin://')">添加客服微信</v-btn>
      </section>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, nextTick } from "vue";
import { gsap } from "gsap";
import SplitText from "gsap/SplitText";
import ScrollTrigger from "gsap/ScrollTrigger";
import doraemonUrl from "../assets/doraemon.jpeg";
function go(url: string): void{
  location.href = url
}
gsap.registerPlugin(SplitText, ScrollTrigger);

const features = [
  {
    title: "8 年稳定运行",
    desc: "长期深耕校园跑领域，保持 0 封号纪录，让你的账号安全无忧。",
    path: "M12 2 4 5v6c0 5 3.5 9.7 8 11 4.5-1.3 8-6 8-11V5l-8-3Zm-1 14-4-4 1.4-1.4L11 13.2l5.6-5.6L18 9l-7 7Z",
  },
  {
    title: "任意模式奔跑",
    desc: "元气晨跑、日常普跑完美适配，灵活满足你的所有需求。",
    path: "M13.5 5.5a2 2 0 1 0-2-2 2 2 0 0 0 2 2ZM9.8 8.9 7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3A7.3 7.3 0 0 0 19 13v-2a5.2 5.2 0 0 1-4.4-2.3l-1-1.6a1.9 1.9 0 0 0-2.4-.8l-5.2 2.2V13h2V9.8Z",
  },
  {
    title: "千名学生信赖",
    desc: "口碑见证实力，已帮助 1000+ 名学生轻松完成跑步任务。",
    path: "M16 11a3 3 0 1 0-3-3 3 3 0 0 0 3 3Zm-8 0a3 3 0 1 0-3-3 3 3 0 0 0 3 3Zm0 2c-2.7 0-8 1.3-8 4v3h16v-3c0-2.7-5.3-4-8-4Zm8 0a8 8 0 0 0-1.6.2A5.4 5.4 0 0 1 18 17v3h6v-3c0-2.7-5.3-4-8-4Z",
  },
  {
    title: "全国学校支持",
    desc: "适配全国 500+ 高校，无论规则多复杂，都能精准应对。",
    path: "M12 3 1 9l4 2.2V17l7 4 7-4v-5.8L21 9Zm6.8 6L12 12.8 5.2 9 12 5.2Zm-1.8 6.7-5 2.9-5-2.9v-3.6l5 2.7 5-2.7Z",
  },
  {
    title: "走心定价",
    desc: "坚持一分钱一分货，提供高品质且实惠的校园跑服务。",
    path: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Zm1 17v-2H9v-2h4v-2H9v-2h3.3l-3-6h2.3l2.4 5L16 6h2.3l-3 6H17v2h-4v2h4v2Z",
  },
];

onMounted(async () => {
  await nextTick();

  const split = SplitText.create(".logo-title", { type: "chars" });
  const tl = gsap.timeline();

  tl.from(split.chars, {
    duration: 1,
    opacity: 0,
    scale: () => gsap.utils.random(0.5, 1.5),
    rotation: () => gsap.utils.random(-90, 90),
    x: () => gsap.utils.random(-100, 100),
    y: () => gsap.utils.random(-100, 100),
    stagger: 0.05,
    ease: "back",
  })
    .from(".hero-sub", { duration: 0.8, opacity: 0, y: 20, ease: "power2.out" }, "-=0.4")
    .from(".hero-cta", { duration: 0.6, opacity: 0, y: 16, ease: "power2.out" }, "-=0.5")
    .from(".hero-card", { scale: 1.05, opacity: 0, duration: 1.2, ease: "power3.out" }, 0);

  gsap.fromTo(
    ".feature-card",
    { y: 80, opacity: 0 },
    {
      y: 0, opacity: 1, duration: 0.9, stagger: 0.12, ease: "power3.out",
      scrollTrigger: {
        trigger: ".feature-grid", start: "top 80%",
        scroller: ".v-main", toggleActions: "play none none none",
      },
    }
  );

  gsap.fromTo(
    ".intro-row > *",
    { y: 40, opacity: 0 },
    {
      y: 0, opacity: 1, duration: 0.9, stagger: 0.15, ease: "power3.out",
      scrollTrigger: { trigger: ".intro-row", start: "top 85%", scroller: ".v-main" },
    }
  );

  gsap.fromTo(
    ".contact-item",
    { y: 30, opacity: 0 },
    {
      y: 0, opacity: 1, duration: 0.7, stagger: 0.1, ease: "power2.out",
      scrollTrigger: { trigger: ".contact-grid", start: "top 85%", scroller: ".v-main" },
    }
  );
});
</script>

<style lang="scss" scoped>
/* ===== Vuetify 默认主题色 ===== */
$primary: #1867C0; // Vuetify primary
$primary-dark: #0d47a1;
$primary-light: #e3f2fd;
$ink: #1F1F1F;
$ink-soft: #424242;
$muted: #757575;
$bg: #FAFAFA; // grey-lighten-5
$bg-soft: #F5F5F5; // grey-lighten-4
$cream: #FFFFFF;

.home {
  background: $bg;
  color: $ink;
  font-family:
    "Inter", "PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont,
    sans-serif;
  -webkit-font-smoothing: antialiased;
}

.content-wrapper {
  max-width: 1500px;
  margin: 0 auto;
}

/* ===== 通用按钮 ===== */
.btn-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 44px;
  padding: 0 24px;
  border-radius: 999px;
  border: none;
  background: $primary;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.02em;
  cursor: pointer;
  box-shadow: 0 8px 20px -8px rgba(24, 103, 192, 0.5);
  transition: transform 0.25s ease, background 0.25s ease, box-shadow 0.25s ease;

  &:hover {
    background: $primary-dark;
    transform: translateY(-2px);
    box-shadow: 0 12px 24px -8px rgba(24, 103, 192, 0.6);
  }

  &.dark {
    background: $primary;
  }

  &.large {
    height: 52px;
    padding: 0 32px;
    font-size: 15px;
  }
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: $muted;
  margin: 0 0 14px;

  &.center {
    text-align: center;
  }
}

/* ========================================================
   Section 1 — Hero（哆啦A梦作为背景）
======================================================== */
.section-1 {
  min-height: 100vh;
  padding: 36px 36px 80px;
  display: flex;
  flex-direction: column;
  position: relative;
  background: $bg;
}

.hero-card {
  flex: 1;
  position: relative;
  border-radius: 28px;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  box-shadow: 0 30px 80px -30px rgba(13, 71, 161, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 160px);
}

/* 在背景图上叠一层蓝色渐变蒙层，保证文字可读 */
.hero-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 50% 40%, rgba(255, 255, 255, 0.55), rgba(255, 255, 255, 0.15) 60%, transparent 80%),
    linear-gradient(180deg, rgba(24, 103, 192, 0.25) 0%, rgba(13, 71, 161, 0.55) 100%);
  backdrop-filter: blur(2px);
}

.hero-inner {
  position: relative;
  z-index: 2;
  text-align: center;
  max-width: 720px;
  padding: 0 24px;

  .hero-mark {
    display: inline-block;
    font-size: 22px;
    color: #fff;
    margin-bottom: 18px;
    opacity: 0.9;
    text-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
  }

  .logo-title {
    font-size: clamp(40px, 6vw, 80px);
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.05;
    margin: 0 0 22px;
    color: #fff;
    text-shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
  }

  .hero-sub {
    font-size: 16px;
    line-height: 1.7;
    color: rgba(255, 255, 255, 0.92);
    margin: 0 auto 32px;
    max-width: 480px;
    text-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
  }

  .hero-cta {
    background: #fff;
    color: $primary;
    box-shadow: 0 12px 30px -10px rgba(0, 0, 0, 0.3);

    &:hover {
      background: $primary-light;
      color: $primary-dark;
    }
  }
}

.continue-scroll {
  position: absolute;
  bottom: 18px;
  left: 0;
  right: 0;
  margin: auto;
  width: fit-content;
  color: $muted;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 12px;
  letter-spacing: 0.1em;
  animation: continue-loop 2.4s ease-in-out infinite;

  svg {
    margin-bottom: 4px;
  }

  p {
    margin: 0;
  }
}

@keyframes continue-loop {

  0%,
  100% {
    opacity: 0.4;
    transform: translateY(-4px);
  }

  50% {
    opacity: 1;
    transform: translateY(4px);
  }
}

/* ========================================================
   Section 2 — Features
======================================================== */
.section-2 {
  padding: 110px 36px;
}

.intro-row {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 60px;
  align-items: end;
  margin-bottom: 56px;

  .intro-title {
    font-size: clamp(36px, 5vw, 64px);
    font-weight: 500;
    line-height: 1.05;
    letter-spacing: -0.02em;
    margin: 0 0 24px;
    color: $ink;
  }

  .intro-right {
    color: $ink-soft;
    font-size: 16px;
    line-height: 1.7;
    margin: 0;
    max-width: 460px;
  }
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
}

.feature-card {
  background: $primary;
  color: #fff;
  border-radius: 22px;
  padding: 36px 30px;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: transform 0.5s cubic-bezier(0.19, 1, 0.22, 1),
    box-shadow 0.5s ease;

  &.is-light {
    background: #fff;
    color: $ink;
    border: 1px solid rgba(24, 103, 192, 0.12);

    .feature-desc {
      color: $ink-soft;
    }

    .feature-icon {
      background: rgba(24, 103, 192, 0.1);
      color: $primary;
    }
  }

  .feature-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 22px;
    color: #fff;
  }

  .feature-title {
    font-size: 22px;
    font-weight: 600;
    margin: 0 0 12px;
    letter-spacing: -0.01em;
  }

  .feature-desc {
    font-size: 14px;
    line-height: 1.65;
    color: rgba(255, 255, 255, 0.82);
    margin: 0;
  }

  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 30px 60px -20px rgba(24, 103, 192, 0.35);
  }
}
/* ========================================================
   Section 3 — Contact
======================================================== */
.section-3 {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 80px 24px;
}

.contact-title {
  font-size: clamp(40px, 5vw, 68px);
  font-weight: 500;
  letter-spacing: -0.02em;
  margin: 0 0 60px;
  color: $ink;
}

.contact-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  max-width: 980px;
  margin: 0 auto 50px;
}

.contact-item {
  background: #fff;
  border-radius: 20px;
  padding: 34px 24px;
  text-align: left;
  border: 1px solid rgba(24, 103, 192, 0.1);
  box-shadow: 0 10px 30px -15px rgba(24, 103, 192, 0.18);

  .contact-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: $muted;
    margin: 0 0 12px;
  }

  .contact-value {
    font-size: 17px;
    font-weight: 600;
    color: $ink;
    margin: 0;
  }
}

/* ========================================================
   Responsive
======================================================== */
@media (max-width: 960px) {

  .intro-row,
  .feature-grid,
  .contact-grid {
    grid-template-columns: 1fr;
  }

  .section-1 {
    padding: 16px 16px 60px;
  }

  .hero-card {
    min-height: calc(100vh - 100px);
    border-radius: 22px;
  }
}
</style>
