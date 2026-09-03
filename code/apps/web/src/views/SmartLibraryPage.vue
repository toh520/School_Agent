<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  borrowLibraryBook,
  fetchLibraryBooks,
  fetchLibraryLoans,
  recommendLibraryBooks,
  returnLibraryLoan,
} from '../api/library'
import type { MeData, UserSummary } from '../types/identity'
import type { LibraryBook, LibraryLoan, LibraryRecommendation } from '../types/library'

defineProps<{ user: UserSummary; me: MeData }>()

const activeView = ref<'catalog' | 'assistant' | 'loans'>('catalog')
const books = ref<LibraryBook[]>([])
const loans = ref<LibraryLoan[]>([])
const loading = ref(false)
const borrowingId = ref('')
const returningId = ref('')
const query = ref('')
const category = ref('ALL')
const tag = ref('ALL')
const availableOnly = ref(false)
const selectedBook = ref<LibraryBook | null>(null)
const detailOpen = ref(false)
const requirement = ref('')
const recommending = ref(false)
const recommendations = ref<LibraryRecommendation[]>([])

const categories = computed(() =>
  [...new Set(books.value.map((book) => book.category).filter(Boolean))].sort(),
)
const tags = computed(() =>
  [...new Set(books.value.flatMap((book) => book.tags).filter(Boolean))].sort(),
)
const filteredBooks = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return books.value.filter((book) => {
    const searchable = [
      book.name,
      book.isbn,
      book.publisher,
      book.summary,
      ...book.authors,
      ...book.tags,
    ]
      .join(' ')
      .toLowerCase()
    return (
      (!keyword || searchable.includes(keyword)) &&
      (category.value === 'ALL' || book.category === category.value) &&
      (tag.value === 'ALL' || book.tags.includes(tag.value)) &&
      (!availableOnly.value || book.available)
    )
  })
})
const currentLoans = computed(() => loans.value.filter((loan) => loan.status === 'BORROWED'))
const returnedLoans = computed(() => loans.value.filter((loan) => loan.status === 'RETURNED'))

function openBook(book: LibraryBook): void {
  selectedBook.value = book
  detailOpen.value = true
}

function openRecommendation(item: LibraryRecommendation): void {
  if (item.sourceType !== 'LIBRARY' || !item.bookId) return
  const book = books.value.find((candidate) => candidate.id === item.bookId)
  if (book) openBook(book)
}

async function reload(): Promise<void> {
  ;[books.value, loans.value] = await Promise.all([fetchLibraryBooks(), fetchLibraryLoans()])
  if (selectedBook.value) {
    selectedBook.value = books.value.find((book) => book.id === selectedBook.value?.id) ?? null
  }
}

async function borrow(book: LibraryBook): Promise<void> {
  if (!book.available) return
  try {
    await ElMessageBox.confirm(
      `确认借阅《${book.name}》？借阅后可在“我的借阅”中归还。`,
      '确认借阅',
      { confirmButtonText: '确认借阅', cancelButtonText: '取消', type: 'info' },
    )
  } catch {
    return
  }
  borrowingId.value = book.id
  try {
    await borrowLibraryBook(book.id)
    await reload()
    ElMessage.success('借阅成功')
  } catch {
    ElMessage.error('借阅失败：可能已无库存或你已借阅过这本书')
  } finally {
    borrowingId.value = ''
  }
}

async function returnBook(loan: LibraryLoan): Promise<void> {
  returningId.value = loan.id
  try {
    await returnLibraryLoan(loan.id)
    await reload()
    ElMessage.success('归还成功')
  } catch {
    ElMessage.error('归还失败，请刷新后重试')
  } finally {
    returningId.value = ''
  }
}

async function generateRecommendations(): Promise<void> {
  if (requirement.value.trim().length < 5) {
    ElMessage.warning('请用一句话描述你想读的书')
    return
  }
  recommending.value = true
  try {
    recommendations.value = await recommendLibraryBooks(requirement.value.trim(), books.value)
    if (!recommendations.value.length) ElMessage.warning('暂未找到足够匹配的书籍，请换一种描述')
  } catch {
    recommendations.value = []
    ElMessage.error('AI 推荐暂时不可用，你仍然可以查询馆藏')
  } finally {
    recommending.value = false
  }
}

function formatTime(value: string | null): string {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

onMounted(async () => {
  loading.value = true
  try {
    await reload()
  } catch {
    ElMessage.error('智慧图书馆加载失败，请确认服务正在运行')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="module-page module-library library-demo" aria-labelledby="library-title">
    <header class="module-hero library-hero">
      <div>
        <p class="page-kicker">Smart library · 馆藏与选书</p>
        <h1 id="library-title">从真实馆藏里，找到此刻需要的书。</h1>
        <p>直接查书，或把阅读期待交给 AI。推荐始终先看馆内，借阅状态以当前库存为准。</p>
      </div>
      <div class="library-counter">
        <span>正在借阅</span><strong>{{ currentLoans.length }}</strong
        ><small>本</small>
      </div>
    </header>

    <nav class="module-tabs library-tabs" aria-label="智慧图书馆功能">
      <button :class="{ active: activeView === 'catalog' }" @click="activeView = 'catalog'">
        馆藏查询
      </button>
      <button :class="{ active: activeView === 'assistant' }" @click="activeView = 'assistant'">
        AI 推荐
      </button>
      <button :class="{ active: activeView === 'loans' }" @click="activeView = 'loans'">
        我的借阅 <span v-if="currentLoans.length">{{ currentLoans.length }}</span>
      </button>
    </nav>

    <section v-if="activeView === 'catalog'" v-loading="loading" class="library-section">
      <div class="catalog-tools">
        <el-input
          v-model="query"
          clearable
          size="large"
          placeholder="搜索书名、作者、ISBN、出版社或关键词"
        />
        <el-select v-model="category" size="large"
          ><el-option label="全部类别" value="ALL" /><el-option
            v-for="item in categories"
            :key="item"
            :label="item"
            :value="item"
        /></el-select>
        <el-select v-model="tag" size="large"
          ><el-option label="全部标签" value="ALL" /><el-option
            v-for="item in tags"
            :key="item"
            :label="item"
            :value="item"
        /></el-select>
        <el-checkbox v-model="availableOnly" border size="large">只看可借</el-checkbox>
      </div>
      <p class="catalog-result">找到 {{ filteredBooks.length }} 本馆藏</p>
      <el-empty v-if="!filteredBooks.length && !loading" description="没有符合当前条件的馆藏" />
      <div v-else class="book-grid">
        <article
          v-for="book in filteredBooks"
          :key="book.id"
          class="book-card"
          @click="openBook(book)"
        >
          <figure class="book-cover">
            <img v-if="book.coverImage" :src="book.coverImage" :alt="`${book.name}封面`" /><span>{{
              book.name.slice(0, 1)
            }}</span>
          </figure>
          <div class="book-card-copy">
            <div class="book-card-status">
              <span>{{ book.category || '未分类' }}</span
              ><em :class="{ empty: !book.available }">{{
                book.available ? `可借 ${book.availableCount}` : '已借完'
              }}</em>
            </div>
            <h2>{{ book.name }}</h2>
            <p class="book-authors">{{ book.authors.join('、') }}</p>
            <p class="book-summary">{{ book.summary || '暂无内容简介' }}</p>
            <div class="tag-row">
              <span v-for="item in book.tags.slice(0, 3)" :key="item">{{ item }}</span>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section v-else-if="activeView === 'assistant'" class="library-section ai-library">
      <div class="ai-request-card">
        <div>
          <p class="page-kicker">Describe the reading mood</p>
          <h2>说说你现在想读什么</h2>
          <p>可以描述主题、情绪、用途、语言或喜欢的叙事方式，不必填写固定条件。</p>
        </div>
        <el-input
          v-model="requirement"
          type="textarea"
          :rows="4"
          maxlength="500"
          show-word-limit
          placeholder="例如：我想读一本节奏快、反转多的中文悬疑小说，最好适合周末一口气读完。"
        />
        <el-button
          type="primary"
          size="large"
          :loading="recommending"
          @click="generateRecommendations"
          >{{ recommendations.length ? '重新推荐' : '开始推荐' }}</el-button
        >
      </div>
      <div v-if="recommendations.length" class="recommendation-heading">
        <div>
          <p class="page-kicker">Ranked for this request</p>
          <h2>为你找到 {{ recommendations.length }} 本</h2>
        </div>
        <p>馆内优先 · 按内容适配度排序</p>
      </div>
      <div class="recommendation-list">
        <article
          v-for="(item, index) in recommendations"
          :key="item.key"
          class="recommendation-card"
          :class="{ external: item.sourceType === 'EXTERNAL' }"
          @click="openRecommendation(item)"
        >
          <span class="rank">{{ String(index + 1).padStart(2, '0') }}</span>
          <figure class="recommend-cover">
            <img v-if="item.coverImage" :src="item.coverImage" :alt="`${item.name}封面`" /><span>{{
              item.name.slice(0, 1)
            }}</span>
          </figure>
          <div class="recommend-copy">
            <div class="recommend-labels">
              <span :class="item.sourceType.toLowerCase()">{{
                item.sourceType === 'LIBRARY' ? '馆内可查' : '馆外推荐'
              }}</span
              ><strong v-if="item.featured">特别推荐</strong><em>{{ item.score }}% 匹配</em>
            </div>
            <h3>{{ item.name }}</h3>
            <p class="book-authors">{{ item.authors.join('、') || '作者信息暂缺' }}</p>
            <p class="recommend-reason">{{ item.reason }}</p>
            <div class="recommend-actions">
              <el-button
                v-if="item.sourceType === 'LIBRARY'"
                type="primary"
                plain
                @click.stop="openRecommendation(item)"
                >查看馆藏与借阅</el-button
              ><a v-else :href="item.externalUrl" target="_blank" rel="noreferrer" @click.stop
                >在 Open Library 查看</a
              >
            </div>
          </div>
        </article>
      </div>
    </section>

    <section v-else class="library-section loans-section">
      <header class="section-heading">
        <div>
          <p class="page-kicker">Borrowing record</p>
          <h2>我的借阅</h2>
        </div>
        <p>借阅和归还会即时更新馆藏数量。</p>
      </header>
      <el-empty v-if="!loans.length" description="还没有借阅记录，可以先去馆藏中选一本书" />
      <template v-else>
        <h3 v-if="currentLoans.length" class="loan-group-title">
          正在借阅 · {{ currentLoans.length }}
        </h3>
        <article v-for="loan in currentLoans" :key="loan.id" class="loan-row">
          <figure class="loan-cover">
            <img v-if="loan.coverImage" :src="loan.coverImage" alt="" /><span>{{
              loan.bookName.slice(0, 1)
            }}</span>
          </figure>
          <div>
            <h4>{{ loan.bookName }}</h4>
            <p>{{ loan.authors }}</p>
            <small>{{ loan.callNumber }} · {{ loan.location }}</small>
          </div>
          <time>借阅于 {{ formatTime(loan.borrowedAt) }}</time>
          <el-button type="primary" :loading="returningId === loan.id" @click="returnBook(loan)"
            >归还</el-button
          >
        </article>
        <h3 v-if="returnedLoans.length" class="loan-group-title returned">
          历史记录 · {{ returnedLoans.length }}
        </h3>
        <article v-for="loan in returnedLoans" :key="loan.id" class="loan-row returned-row">
          <figure class="loan-cover">
            <img v-if="loan.coverImage" :src="loan.coverImage" alt="" /><span>{{
              loan.bookName.slice(0, 1)
            }}</span>
          </figure>
          <div>
            <h4>{{ loan.bookName }}</h4>
            <p>{{ loan.authors }}</p>
          </div>
          <time
            >{{ formatTime(loan.borrowedAt) }} 借阅<br />{{
              formatTime(loan.returnedAt)
            }}
            归还</time
          ><el-tag type="info">已归还</el-tag>
        </article>
      </template>
    </section>

    <el-drawer v-model="detailOpen" size="min(680px, 94vw)">
      <template #header><span class="drawer-kicker">馆藏详情</span></template>
      <div v-if="selectedBook" class="book-detail">
        <div class="detail-lead">
          <figure class="detail-cover">
            <img
              v-if="selectedBook.coverImage"
              :src="selectedBook.coverImage"
              :alt="`${selectedBook.name}封面`"
            /><span>{{ selectedBook.name.slice(0, 1) }}</span>
          </figure>
          <div>
            <p>{{ selectedBook.category }}</p>
            <h2>{{ selectedBook.name }}</h2>
            <h3>{{ selectedBook.authors.join('、') }}</h3>
            <div class="tag-row">
              <span v-for="item in selectedBook.tags" :key="item">{{ item }}</span>
            </div>
          </div>
        </div>
        <section class="detail-section">
          <h3>内容介绍</h3>
          <p>{{ selectedBook.summary || '暂无内容介绍' }}</p>
        </section>
        <dl class="book-metadata">
          <div>
            <dt>出版社</dt>
            <dd>{{ selectedBook.publisher || '—' }}</dd>
          </div>
          <div>
            <dt>出版信息</dt>
            <dd>
              {{ selectedBook.publishedYear || '—' }} · {{ selectedBook.edition || '版本未注明' }}
            </dd>
          </div>
          <div>
            <dt>ISBN</dt>
            <dd>{{ selectedBook.isbn }}</dd>
          </div>
          <div>
            <dt>语言</dt>
            <dd>{{ selectedBook.language || '—' }}</dd>
          </div>
          <div>
            <dt>索书号</dt>
            <dd>{{ selectedBook.callNumber }}</dd>
          </div>
          <div>
            <dt>书架位置</dt>
            <dd>{{ selectedBook.location }}</dd>
          </div>
        </dl>
        <div class="borrow-panel">
          <div>
            <span>馆藏 {{ selectedBook.totalCount }} 本</span
            ><strong :class="{ empty: !selectedBook.available }">{{
              selectedBook.available ? `当前可借 ${selectedBook.availableCount} 本` : '当前已借完'
            }}</strong>
          </div>
          <el-button
            type="primary"
            size="large"
            :disabled="!selectedBook.available"
            :loading="borrowingId === selectedBook.id"
            @click="borrow(selectedBook)"
            >借阅这本书</el-button
          >
        </div>
      </div>
    </el-drawer>
  </section>
</template>
