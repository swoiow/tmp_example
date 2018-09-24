<template>
  <div id="bottom"> Copyright © {{ new Date().getFullYear() }} {{ name }}</div>
</template>

<script>
  export default {
    name: 'bottom',
    data() {
      return {
        name: "PYLab.me",
      }
    }
  }
</script>

<style>
  #bottom {
    font-size: x-small;
    position: absolute;
    bottom: 1rem;
    text-align: left;
    text-shadow: 0 0 0.2em #7f7a7a;
  }
</style>
