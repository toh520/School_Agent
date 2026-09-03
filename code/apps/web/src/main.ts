import { createPinia } from 'pinia'
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './styles.css'
import './responsive.css'
import './admin.css'
import './agent.css'
import './student.css'
import './library.css'

createApp(App).use(createPinia()).use(ElementPlus).use(router).mount('#app')
