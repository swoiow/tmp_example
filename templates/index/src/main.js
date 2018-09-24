import Vue from 'vue'
import App from './App.vue'
import AppFooter from './AppFooter.vue'
import Velocity from 'velocity-animate'

new Vue({
  el: '#app',
  render: h => h(App)
});

new Vue({
  el: '#bottom',
  render: h => h(AppFooter)
});
