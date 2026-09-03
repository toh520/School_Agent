<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  addCartItem,
  deleteCartItem,
  fetchCart,
  fetchFoods,
  placeDemoOrder,
  recommendMeals,
  updateCartItem,
} from '../api/canteen'
import type { Cart, DemoOrder, Food, MealCombination } from '../types/canteen'
import type { MeData, UserSummary } from '../types/identity'

const props = defineProps<{ user: UserSummary; me: MeData }>()
const activeView = ref<'menu' | 'assistant' | 'cart'>('menu')
const foods = ref<Food[]>([])
const cart = ref<Cart>({ items: [], totalQuantity: 0, totalAmount: 0 })
const loading = ref(false)
const recommending = ref(false)
const ordering = ref(false)
const query = ref('')
const category = ref('ALL')
const recommendations = ref<MealCombination[]>([])
const excludedCombinations = ref<string[]>([])
const lastOrder = ref<DemoOrder | null>(null)
const requestForm = reactive({
  budget: 25,
  dinerCount: 1,
  tastes: [] as string[],
  spiceLevel: '',
  goals: [] as string[],
  preferredIngredients: [] as string[],
  excludedIngredients: [] as string[],
  mealScale: '',
  extraRequirements: '',
})

const categories = [
  ['ALL', '全部'],
  ['STAPLE', '主食'],
  ['MEAT', '荤菜'],
  ['VEGETABLE', '素菜'],
  ['SOUP', '汤品'],
  ['DRINK', '饮品'],
  ['SNACK', '小吃'],
]
const categoryLabels = Object.fromEntries(categories)
const spiceLabels: Record<string, string> = {
  NONE: '不辣',
  MILD: '微辣',
  MEDIUM: '中辣',
  HOT: '重辣',
}
const nutritionLabels: Record<string, string> = {
  UNKNOWN: '未知',
  LOW: '较低',
  MEDIUM: '适中',
  HIGH: '较高',
}
const goalOptions = ['吃饱', '搭配均衡', '低热量', '高蛋白', '清淡饮食']
const scaleOptions = [
  ['SIMPLE', '简单一餐'],
  ['STANDARD', '标准搭配'],
  ['RICH', '丰富一些'],
]
const filteredFoods = computed(() =>
  foods.value.filter((food) => {
    const matchesCategory = category.value === 'ALL' || food.category === category.value
    const keyword = query.value.trim().toLowerCase()
    return (
      matchesCategory &&
      (!keyword ||
        [food.name, food.description, ...food.ingredients, ...food.tastes].some((value) =>
          value.toLowerCase().includes(keyword),
        ))
    )
  }),
)
const foodMap = computed(() => new Map(foods.value.map((food) => [food.id, food])))

function matchingAllergens(food: Food): string[] {
  const profile = new Set(props.me.preference.allergens.map((item) => item.toLowerCase()))
  return food.allergens.filter((item) => profile.has(item.toLowerCase()))
}

async function addFood(food: Food, fromAi = false, quantity = 1): Promise<void> {
  const risks = matchingAllergens(food)
  let confirmed = false
  if (risks.length) {
    if (fromAi) return
    try {
      await ElMessageBox.confirm(
        `“${food.name}”含有你的过敏原：${risks.join('、')}。仍要加入购物车吗？`,
        '过敏风险确认',
        { type: 'warning', confirmButtonText: '了解风险，仍然加入', cancelButtonText: '取消' },
      )
      confirmed = true
    } catch {
      return
    }
  }
  cart.value = await addCartItem(food.id, quantity, confirmed)
  if (!fromAi) ElMessage.success(`${food.name}已加入购物车`)
}

async function generateRecommendations(retry = false): Promise<void> {
  if (retry && !requestForm.extraRequirements.trim()) {
    ElMessage.warning('请先补充你不满意的原因或新的要求')
    return
  }
  recommending.value = true
  try {
    if (retry) excludedCombinations.value.push(...recommendations.value.map((item) => item.key))
    recommendations.value = await recommendMeals({
      foods: foods.value,
      allergens: props.me.preference.allergens,
      avoidances: props.me.preference.avoidances,
      budget: requestForm.budget,
      dinerCount: requestForm.dinerCount,
      tastes: requestForm.tastes,
      spiceLevel: requestForm.spiceLevel || null,
      goals: requestForm.goals,
      preferredIngredients: requestForm.preferredIngredients,
      excludedIngredients: requestForm.excludedIngredients,
      mealScale: requestForm.mealScale,
      extraRequirements: requestForm.extraRequirements,
      excludedCombinations: excludedCombinations.value,
    })
    if (!recommendations.value.length)
      ElMessage.warning('当前餐品无法满足条件，请提高预算或调整要求')
  } catch {
    recommendations.value = []
    ElMessage.error('AI 推荐暂时不可用，你仍然可以手动选择餐品')
  } finally {
    recommending.value = false
  }
}

async function addCombination(combination: MealCombination): Promise<void> {
  for (const foodId of combination.foodIds) {
    const food = foodMap.value.get(foodId)
    if (food) await addFood(food, true, combination.quantities[foodId] ?? 1)
  }
  activeView.value = 'cart'
  ElMessage.success('推荐组合已加入购物车')
}

async function changeQuantity(itemId: string, value: number | undefined): Promise<void> {
  if (value) cart.value = await updateCartItem(itemId, value)
}

async function removeItem(itemId: string): Promise<void> {
  cart.value = await deleteCartItem(itemId)
}

async function submitOrder(): Promise<void> {
  ordering.value = true
  try {
    lastOrder.value = await placeDemoOrder()
    cart.value = { items: [], totalQuantity: 0, totalAmount: 0 }
    ElMessage.success('下单成功')
  } finally {
    ordering.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    ;[foods.value, cart.value] = await Promise.all([fetchFoods(), fetchCart()])
  } catch {
    ElMessage.error('智能食堂加载失败，请确认服务正在运行')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="module-page module-canteen canteen-demo" aria-labelledby="canteen-title">
    <header class="module-hero canteen-hero">
      <div>
        <p class="page-kicker">One canteen · 今日菜单</p>
        <h1 id="canteen-title">先看今天吃什么，再决定这一餐。</h1>
        <p>所有餐品由管理员维护。你可以直接挑选，也可以让 AI 在预算、安全和口味范围内组合。</p>
      </div>
      <div class="tray-counter">
        <span>购物车</span><strong>{{ cart.totalQuantity }}</strong
        ><small>件餐品</small>
      </div>
    </header>

    <nav class="module-tabs" aria-label="智能食堂功能">
      <button :class="{ active: activeView === 'menu' }" @click="activeView = 'menu'">
        餐品大厅
      </button>
      <button :class="{ active: activeView === 'assistant' }" @click="activeView = 'assistant'">
        AI 帮我选
      </button>
      <button :class="{ active: activeView === 'cart' }" @click="activeView = 'cart'">
        购物车（{{ cart.totalQuantity }}）
      </button>
      <router-link to="/orders">我的订单</router-link>
    </nav>

    <div v-if="activeView === 'menu'" v-loading="loading">
      <div class="menu-toolbar">
        <div class="category-strip">
          <button
            v-for="item in categories"
            :key="item[0]"
            :class="{ active: category === item[0] }"
            @click="category = item[0]"
          >
            {{ item[1] }}
          </button>
        </div>
        <el-input v-model="query" clearable placeholder="搜索餐品、口味或食材" />
      </div>
      <div class="food-grid">
        <article v-for="food in filteredFoods" :key="food.id" class="food-card">
          <div class="food-photo">
            <img :src="food.imageUrl" :alt="food.name" /><span v-if="food.featured">今日热门</span>
          </div>
          <div class="food-card-body">
            <div class="food-title">
              <div>
                <small
                  >{{ categoryLabels[food.category] }} · {{ spiceLabels[food.spiceLevel] }}</small
                >
                <h2>{{ food.name }}</h2>
              </div>
              <strong>¥{{ food.price.toFixed(2) }}</strong>
            </div>
            <p>{{ food.description }}</p>
            <div class="food-tags">
              <span v-for="taste in food.tastes" :key="taste">{{ taste }}</span
              ><span>热量{{ nutritionLabels[food.energyLevel] }}</span>
            </div>
            <p v-if="matchingAllergens(food).length" class="allergen-alert">
              含个人档案过敏原：{{ matchingAllergens(food).join('、') }}
            </p>
            <button class="food-add" @click="addFood(food)">加入购物车</button>
          </div>
        </article>
      </div>
    </div>

    <div v-else-if="activeView === 'assistant'" class="ai-meal-layout">
      <section class="module-panel meal-request-card">
        <p class="panel-label">本次用餐条件</p>
        <h2>告诉 AI 这一餐想怎么吃</h2>
        <div class="meal-form-preview">
          <label
            >本餐预算<el-input-number v-model="requestForm.budget" :min="5" :max="100"
          /></label>
          <label
            >用餐人数<el-input-number v-model="requestForm.dinerCount" :min="1" :max="20"
          /></label>
          <label
            >辣度<el-select v-model="requestForm.spiceLevel" placeholder="请选择辣度"
              ><el-option label="不限" value="" /><el-option
                v-for="(label, value) in spiceLabels"
                :key="value"
                :label="label"
                :value="value" /></el-select
          ></label>
          <label class="wide-field"
            >想吃的口味<el-select
              v-model="requestForm.tastes"
              multiple
              allow-create
              filterable
              placeholder="例如清淡、酸甜、咸鲜"
          /></label>
          <label class="wide-field"
            >饮食目标<el-select
              v-model="requestForm.goals"
              multiple
              clearable
              placeholder="选填，不选择表示不限"
              ><el-option v-for="goal in goalOptions" :key="goal" :label="goal" :value="goal"
            /></el-select>
          </label>
          <label
            >想吃的食材<el-select
              v-model="requestForm.preferredIngredients"
              multiple
              filterable
              allow-create
              clearable
              placeholder="选填，例如牛肉、青菜"
          /></label>
          <label
            >不想吃的食材<el-select
              v-model="requestForm.excludedIngredients"
              multiple
              filterable
              allow-create
              clearable
              placeholder="选填，填写后强制排除"
          /></label>
          <label class="wide-field"
            >套餐规模<el-radio-group v-model="requestForm.mealScale">
              <el-radio-button value="">不限</el-radio-button>
              <el-radio-button v-for="item in scaleOptions" :key="item[0]" :value="item[0]">{{
                item[1]
              }}</el-radio-button>
            </el-radio-group></label
          >
          <label class="wide-field"
            >补充要求<el-input
              v-model="requestForm.extraRequirements"
              type="textarea"
              :rows="3"
              placeholder="例如不想吃面，想要一份热汤"
          /></label>
        </div>
        <el-button type="primary" :loading="recommending" @click="generateRecommendations(false)"
          >生成 3 个推荐组合</el-button
        >
        <div class="ai-safety-line">
          <strong>安全规则</strong
          ><span
            >AI 已强制排除：{{
              me.preference.allergens.length ? me.preference.allergens.join('、') : '暂无个人过敏原'
            }}</span
          >
        </div>
      </section>
      <section class="recommendation-stack">
        <article
          v-for="combination in recommendations"
          :key="combination.key"
          class="meal-combination"
        >
          <div>
            <small>AI 推荐组合</small>
            <h3>{{ combination.title }}</h3>
            <p>{{ combination.reason }}</p>
            <div class="reason-tags">
              <span v-for="item in combination.matchedRequirements" :key="item">✓ {{ item }}</span>
              <span v-for="item in combination.limitations" :key="item" class="limitation"
                >说明：{{ item }}</span
              >
            </div>
          </div>
          <ul>
            <li v-for="foodId in combination.foodIds" :key="foodId">
              <img :src="foodMap.get(foodId)?.imageUrl" alt="" /><span
                >{{ foodMap.get(foodId)?.name }} × {{ combination.quantities[foodId] ?? 1 }}</span
              >
            </li>
          </ul>
          <footer>
            <span>¥{{ combination.totalPrice.toFixed(2) }} · 营养信息为定性参考</span
            ><button @click="addCombination(combination)">选择这套</button>
          </footer>
        </article>
        <div v-if="recommendations.length" class="retry-recommendation">
          <p>三个组合都不满意？在左侧补充新的要求，再让 AI 换一批。</p>
          <el-button :loading="recommending" @click="generateRecommendations(true)"
            >都不满意，重新推荐</el-button
          >
        </div>
        <div v-else class="recommendation-empty">
          <span>食</span>
          <p>填写本餐条件后，这里会出现三个真实在售餐品组合。</p>
        </div>
      </section>
    </div>

    <section v-else class="cart-board">
      <div v-if="lastOrder" class="order-success">
        <span>✓</span>
        <div>
          <small>DEMO ORDER</small>
          <h2>已下单</h2>
          <p>订单号 {{ lastOrder.orderNumber }} · 合计 ¥{{ lastOrder.totalAmount.toFixed(2) }}</p>
        </div>
      </div>
      <div v-if="cart.items.length" class="cart-list">
        <article v-for="item in cart.items" :key="item.id">
          <img :src="item.food.imageUrl" :alt="item.food.name" />
          <div>
            <h3>{{ item.food.name }}</h3>
            <p>¥{{ item.food.price.toFixed(2) }} / 份</p>
          </div>
          <el-input-number
            :model-value="item.quantity"
            :min="1"
            :max="20"
            @change="(value: number | undefined) => changeQuantity(item.id, value)"
          /><strong>¥{{ item.subtotal.toFixed(2) }}</strong
          ><el-button link type="danger" @click="removeItem(item.id)">移除</el-button>
        </article>
        <footer>
          <div>
            <span>共 {{ cart.totalQuantity }} 件</span
            ><strong>合计 ¥{{ cart.totalAmount.toFixed(2) }}</strong>
          </div>
          <el-button type="primary" size="large" :loading="ordering" @click="submitOrder"
            >确认下单</el-button
          >
        </footer>
      </div>
      <div v-else-if="!lastOrder" class="recommendation-empty">
        <span>篮</span>
        <p>购物车还是空的。去餐品大厅挑选，或者让 AI 帮你组合一餐。</p>
        <el-button @click="activeView = 'menu'">去选餐</el-button>
      </div>
    </section>
  </section>
</template>
