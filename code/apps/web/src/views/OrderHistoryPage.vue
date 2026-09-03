<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchOrders } from '../api/canteen'
import type { DemoOrder } from '../types/canteen'

const orders = ref<DemoOrder[]>([])
const loading = ref(true)
const totalSpent = computed(() => orders.value.reduce((sum, order) => sum + order.totalAmount, 0))

function formatTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

onMounted(async () => {
  try {
    orders.value = await fetchOrders()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '订单记录加载失败')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="order-history-page" v-loading="loading">
    <header class="order-history-hero">
      <div>
        <p class="page-kicker">Meal archive · 用餐记录</p>
        <h1>我的订单</h1>
        <p>下单后形成不可变的餐品快照，菜单后续修改不会影响历史记录。</p>
      </div>
      <dl>
        <div>
          <dt>累计订单</dt>
          <dd>{{ orders.length }}</dd>
        </div>
        <div>
          <dt>累计金额</dt>
          <dd>¥{{ totalSpent.toFixed(2) }}</dd>
        </div>
      </dl>
    </header>

    <el-empty v-if="!orders.length && !loading" description="暂无订单，先去智能食堂选择一餐" />
    <div v-else class="order-history-list">
      <article v-for="order in orders" :key="order.id" class="order-history-card">
        <header>
          <div>
            <small>订单编号</small><strong>{{ order.orderNumber }}</strong>
          </div>
          <div class="order-meta">
            <el-tag type="success" effect="plain">已下单</el-tag>
            <time>{{ formatTime(order.createdAt) }}</time>
          </div>
        </header>
        <ul>
          <li v-for="item in order.items" :key="`${order.id}-${item.foodName}`">
            <img :src="item.imageUrl" alt="" />
            <span
              ><strong>{{ item.foodName }}</strong
              ><small>¥{{ item.unitPrice.toFixed(2) }} × {{ item.quantity }}</small></span
            >
            <b>¥{{ (item.unitPrice * item.quantity).toFixed(2) }}</b>
          </li>
        </ul>
        <footer>
          <span>共 {{ order.items.reduce((sum, item) => sum + item.quantity, 0) }} 份</span
          ><strong>合计 ¥{{ order.totalAmount.toFixed(2) }}</strong>
        </footer>
      </article>
    </div>
  </section>
</template>
