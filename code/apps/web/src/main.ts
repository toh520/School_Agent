import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { ElAlert, ElButton, ElSkeleton, ElTag } from 'element-plus'
import 'element-plus/theme-chalk/base.css'
import 'element-plus/theme-chalk/el-alert.css'
import 'element-plus/theme-chalk/el-button.css'
import 'element-plus/theme-chalk/el-skeleton.css'
import 'element-plus/theme-chalk/el-tag.css'

import App from './App.vue'
import './styles.css'

createApp(App)
  .use(createPinia())
  .component(ElAlert.name!, ElAlert)
  .component(ElButton.name!, ElButton)
  .component(ElSkeleton.name!, ElSkeleton)
  .component(ElTag.name!, ElTag)
  .mount('#app')
