import { createRouter, createWebHistory } from 'vue-router'

import CampusAssistantPage from './views/CampusAssistantPage.vue'
import ExamAssistantPage from './views/ExamAssistantPage.vue'
import PersonalCenterPage from './views/PersonalCenterPage.vue'
import OrderHistoryPage from './views/OrderHistoryPage.vue'
import SmartCanteenPage from './views/SmartCanteenPage.vue'
import SmartLibraryPage from './views/SmartLibraryPage.vue'
import StudentHomePage from './views/StudentHomePage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/home' },
    { path: '/home', name: 'home', component: StudentHomePage },
    { path: '/canteen', name: 'canteen', component: SmartCanteenPage },
    { path: '/orders', name: 'orders', component: OrderHistoryPage },
    { path: '/campus', name: 'campus', component: CampusAssistantPage },
    { path: '/exam', name: 'exam', component: ExamAssistantPage },
    { path: '/library', name: 'library', component: SmartLibraryPage },
    { path: '/profile', name: 'profile', component: PersonalCenterPage },
    { path: '/:pathMatch(.*)*', redirect: '/home' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
