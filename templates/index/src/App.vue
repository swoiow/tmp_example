<template>
  <div id="app">
    <div class="lead-row">
      Hello<template v-if="!isMobile">,</template>
      <transition
        mode="out-in"
        v-on:before-enter="beforeEnter"
        v-on:enter="enter"
        v-on:leave="leave"
      >
        <span v-bind:class="domId" v-if="show"> {{ flag }} </span>
      </transition>
      <template v-if="!isMobile">
        <div v-bind:class="domId"> !</div>
      </template>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'app',
    data() {
      return {
        domId: "content-label",
        isMobile: false,
        cnt: 0,
        show: true,
        bucket: ["Scrapy", "Puppeteer", "Redis", "Flask", "Tornado", "PostgreSql", "Kafka", "Elasticsearch"],
        flag: "湃森"
      }
    },
    mounted: function () {
      let vm = this;
      vm.$data.show = false
    },
    created() {
      let vm = this;
      vm.$data.isMobile = screen.width <= 760 && true || false;
      // Velocity(el, {opacity: 0}, {
      //   duration: 2000,
      // })
    },
    methods: {
      beforeEnter: function (el) {
        el.style.opacity = 0;
      },
      enter: function (el, done) {
        let vm = this;

        Velocity(el, {opacity: 1}, {
          duration: 2550,
          complete: function () {
            done();
            vm.$data.show = false;
          }
        });
      },
      leave: function (el, done) {
        let vm = this;

        Velocity(el, {opacity: 0}, {
          duration: 800, complete: function () {
            done();
            vm.$data.show = true;
            vm.$data.flag = vm.$data.bucket[vm.$data.cnt];
            vm.$data.cnt += 1;
            if (vm.$data.cnt > vm.$data.bucket.length - 1) {
              vm.$data.cnt = 0;
            }
          }
        });
      },
    }
  }
</script>

<style>
  html {
    -webkit-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%;
    font-family: Helvetica, Tahoma, Arial, STXihei, \\534E\6587\7EC6\9ED1, Microsoft YaHei, \\5FAE\8F6F\96C5\9ED1, sans-serif;
    background-color: #fdf6e3;
    color: #657b83;
    margin: 1em
  }

  .content-label {
    opacity: 1;
    display: inline;
    font-size: 3rem
  }

  .lead-row {
    font-size: 4rem;
    margin-bottom: 5rem
  }

  #app {
    text-align: center;
    background-color: #fdf6e3;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%)
  }
</style>
