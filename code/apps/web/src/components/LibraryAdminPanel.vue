<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createAdminLibraryBook,
  deactivateAdminLibraryBook,
  fetchAdminLibraryBooks,
  updateAdminLibraryBook,
} from '../api/library'
import type { LibraryBook, LibraryBookInput } from '../types/library'

const books = ref<LibraryBook[]>([])
const loading = ref(false)
const saving = ref(false)
const query = ref('')
const drawerOpen = ref(false)
const selected = ref<LibraryBook | null>(null)
const form = reactive<LibraryBookInput>(emptyForm())

function emptyForm(): LibraryBookInput {
  return {
    name: '',
    isbn: '',
    authors: [],
    publisher: '',
    edition: '',
    publishedYear: null,
    language: '中文',
    category: '',
    tags: [],
    summary: '',
    coverImage: '',
    callNumber: '',
    location: '',
    totalCount: 1,
    availableCount: 1,
  }
}

function resetForm(value?: LibraryBook): void {
  Object.assign(
    form,
    value
      ? {
          name: value.name,
          isbn: value.isbn,
          authors: [...value.authors],
          publisher: value.publisher,
          edition: value.edition,
          publishedYear: value.publishedYear,
          language: value.language,
          category: value.category,
          tags: [...value.tags],
          summary: value.summary,
          coverImage: value.coverImage,
          callNumber: value.callNumber,
          location: value.location,
          totalCount: value.totalCount,
          availableCount: value.availableCount,
        }
      : emptyForm(),
  )
}

async function load(): Promise<void> {
  loading.value = true
  try {
    books.value = await fetchAdminLibraryBooks(query.value.trim())
  } catch {
    ElMessage.error('图书加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  selected.value = null
  resetForm()
  drawerOpen.value = true
}

function openEdit(book: LibraryBook): void {
  selected.value = book
  resetForm(book)
  drawerOpen.value = true
}

function validate(): boolean {
  if (!form.name.trim() || !form.isbn.trim() || !form.authors.length || !form.category.trim()) {
    ElMessage.warning('请填写书名、ISBN、作者和类别')
    return false
  }
  if (!form.callNumber.trim() || !form.location.trim()) {
    ElMessage.warning('请填写索书号和书架位置')
    return false
  }
  if (form.availableCount > form.totalCount) {
    ElMessage.warning('可借册数不能超过馆藏总册数')
    return false
  }
  return true
}

async function save(): Promise<void> {
  if (!validate()) return
  saving.value = true
  try {
    if (selected.value) {
      await updateAdminLibraryBook(selected.value.id, { ...form })
      ElMessage.success('图书信息与馆藏已更新')
    } else {
      await createAdminLibraryBook({ ...form })
      ElMessage.success('图书与馆藏已创建')
    }
    drawerOpen.value = false
    await load()
  } catch {
    ElMessage.error('保存失败，请检查 ISBN、库存数量和必填项')
  } finally {
    saving.value = false
  }
}

async function deactivate(book: LibraryBook): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `停用《${book.name}》后，学生将不能查询或借阅。存在未归还记录时系统会拒绝停用。`,
      '确认停用图书',
      { type: 'warning', confirmButtonText: '确认停用', cancelButtonText: '取消' },
    )
    await deactivateAdminLibraryBook(book.id)
    ElMessage.success('图书已停用')
    await load()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error('停用失败：请先处理未归还记录')
  }
}

function chooseCover(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/') || file.size > 1024 * 1024) {
    ElMessage.warning('请选择不超过 1MB 的图片')
    input.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    form.coverImage = String(reader.result)
  }
  reader.readAsDataURL(file)
}

onMounted(load)
</script>

<template>
  <section class="library-admin" v-loading="loading">
    <header class="library-admin-tools">
      <el-input
        v-model="query"
        clearable
        placeholder="搜索书名、作者、ISBN、类别或标签"
        @keyup.enter="load"
      />
      <el-button @click="load">搜索</el-button>
      <el-button type="primary" @click="openCreate">新增图书</el-button>
    </header>

    <el-empty v-if="!books.length && !loading" description="暂无图书，点击右上角新增第一本" />
    <div v-else class="admin-book-list">
      <article v-for="book in books" :key="book.id" class="admin-book-card">
        <figure>
          <img v-if="book.coverImage" :src="book.coverImage" :alt="`${book.name}封面`" /><span>{{
            book.name.slice(0, 1)
          }}</span>
        </figure>
        <section class="bibliographic-half">
          <p class="admin-book-label">书籍信息</p>
          <h2>{{ book.name }}</h2>
          <p>{{ book.authors.join('、') }}</p>
          <dl>
            <div>
              <dt>ISBN</dt>
              <dd>{{ book.isbn }}</dd>
            </div>
            <div>
              <dt>出版</dt>
              <dd>{{ book.publisher || '—' }} · {{ book.publishedYear || '—' }}</dd>
            </div>
            <div>
              <dt>类别</dt>
              <dd>{{ book.category }}</dd>
            </div>
            <div>
              <dt>标签</dt>
              <dd>{{ book.tags.join('、') || '—' }}</dd>
            </div>
          </dl>
        </section>
        <section class="holding-half">
          <p class="admin-book-label">馆藏信息</p>
          <strong :class="{ empty: !book.available }">{{
            book.available ? '当前可借' : '已借完'
          }}</strong>
          <dl>
            <div>
              <dt>索书号</dt>
              <dd>{{ book.callNumber }}</dd>
            </div>
            <div>
              <dt>位置</dt>
              <dd>{{ book.location }}</dd>
            </div>
            <div>
              <dt>馆藏</dt>
              <dd>{{ book.totalCount }} 本</dd>
            </div>
            <div>
              <dt>可借</dt>
              <dd>{{ book.availableCount }} 本</dd>
            </div>
          </dl>
        </section>
        <div class="admin-book-actions">
          <el-button link type="primary" @click="openEdit(book)">编辑</el-button
          ><el-button link type="danger" @click="deactivate(book)">停用</el-button>
        </div>
      </article>
    </div>

    <el-drawer
      v-model="drawerOpen"
      :title="selected ? '编辑图书' : '新增图书'"
      size="min(760px, 94vw)"
    >
      <el-form label-position="top" class="combined-book-form" @submit.prevent="save">
        <section class="form-part">
          <header>
            <span>书</span>
            <div>
              <h3>书籍信息</h3>
              <p>用于搜索、筛选和 AI 内容匹配</p>
            </div>
          </header>
          <div class="form-grid">
            <el-form-item label="封面图片" class="cover-field"
              ><div class="admin-cover-picker">
                <div>
                  <img v-if="form.coverImage" :src="form.coverImage" alt="封面预览" /><span v-else
                    >封面</span
                  >
                </div>
                <label
                  >选择图片<input type="file" accept="image/*" @change="chooseCover"
                /></label></div
            ></el-form-item>
            <div class="form-fields">
              <el-form-item label="书名（必填）"
                ><el-input v-model="form.name" maxlength="120"
              /></el-form-item>
              <el-form-item label="作者（必填）"
                ><el-select
                  v-model="form.authors"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="输入作者后回车"
              /></el-form-item>
              <div class="two-fields">
                <el-form-item label="ISBN（必填）"><el-input v-model="form.isbn" /></el-form-item
                ><el-form-item label="语言"><el-input v-model="form.language" /></el-form-item>
              </div>
            </div>
          </div>
          <div class="two-fields">
            <el-form-item label="出版社"><el-input v-model="form.publisher" /></el-form-item
            ><el-form-item label="出版年份"
              ><el-input-number
                v-model="form.publishedYear"
                :min="1000"
                :max="2100"
                controls-position="right"
            /></el-form-item>
          </div>
          <div class="two-fields">
            <el-form-item label="版本"><el-input v-model="form.edition" /></el-form-item
            ><el-form-item label="类别（必填）"
              ><el-input v-model="form.category" placeholder="例如 小说、名著、计算机"
            /></el-form-item>
          </div>
          <el-form-item label="标签"
            ><el-select
              v-model="form.tags"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入悬疑、爱情等标签后回车"
          /></el-form-item>
          <el-form-item label="内容介绍"
            ><el-input
              v-model="form.summary"
              type="textarea"
              :rows="5"
              maxlength="4000"
              show-word-limit
          /></el-form-item>
        </section>

        <section class="form-part holding-form-part">
          <header>
            <span>藏</span>
            <div>
              <h3>馆藏信息</h3>
              <p>一个图书馆对应一条库存记录</p>
            </div>
          </header>
          <div class="two-fields">
            <el-form-item label="索书号（必填）"
              ><el-input v-model="form.callNumber" placeholder="例如 I5/1984" /></el-form-item
            ><el-form-item label="书架位置（必填）"
              ><el-input v-model="form.location" placeholder="例如 一层文学书架"
            /></el-form-item>
          </div>
          <div class="two-fields">
            <el-form-item label="馆藏总册数"
              ><el-input-number v-model="form.totalCount" :min="0" :max="100000" /></el-form-item
            ><el-form-item label="当前可借册数"
              ><el-input-number v-model="form.availableCount" :min="0" :max="form.totalCount"
            /></el-form-item>
          </div>
        </section>
        <footer class="combined-form-actions">
          <el-button @click="drawerOpen = false">取消</el-button
          ><el-button type="primary" native-type="submit" :loading="saving"
            >保存书籍与馆藏</el-button
          >
        </footer>
      </el-form>
    </el-drawer>
  </section>
</template>

<style scoped>
.library-admin-tools {
  display: grid;
  grid-template-columns: minmax(280px, 440px) auto auto;
  gap: 10px;
  justify-content: end;
  margin-bottom: 20px;
}
.admin-book-list {
  display: grid;
  gap: 12px;
}
.admin-book-card {
  display: grid;
  grid-template-columns: 76px minmax(320px, 1.4fr) minmax(260px, 1fr) 100px;
  gap: 20px;
  align-items: stretch;
  padding: 16px;
  background: #fff;
  border: 1px solid #dfe5ee;
  border-radius: 14px;
}
.admin-book-card figure {
  position: relative;
  display: grid;
  place-items: center;
  overflow: hidden;
  width: 76px;
  height: 108px;
  margin: 0;
  border-radius: 7px;
  background: #334a7d;
  color: #fff;
  font:
    700 26px Georgia,
    serif;
}
.admin-book-card figure img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}
.admin-book-card section {
  min-width: 0;
}
.bibliographic-half {
  padding-right: 20px;
  border-right: 1px solid #e2e8f0;
}
.admin-book-label {
  margin: 0 0 7px;
  color: #3157a4;
  font-size: 11px;
  letter-spacing: 0.12em;
}
.admin-book-card h2 {
  margin: 0 0 4px;
  color: #172554;
  font:
    700 20px Georgia,
    'Noto Serif SC',
    serif;
}
.admin-book-card section > p:not(.admin-book-label) {
  margin: 0;
  color: #64748b;
}
.admin-book-card dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 18px;
  margin: 12px 0 0;
}
.admin-book-card dl div {
  min-width: 0;
}
.admin-book-card dt {
  font-size: 10px;
  color: #94a3b8;
}
.admin-book-card dd {
  overflow: hidden;
  margin: 3px 0 0;
  color: #334155;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.holding-half > strong {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 99px;
  background: #dcfce7;
  color: #166534;
  font-size: 11px;
}
.holding-half > strong.empty {
  background: #fee2e2;
  color: #991b1b;
}
.admin-book-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.form-part {
  padding: 22px;
  margin-bottom: 18px;
  border: 1px solid #dfe5ee;
  border-radius: 14px;
  background: #fff;
}
.form-part > header {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
}
.form-part > header > span {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #172554;
  color: #fff;
  font-family: Georgia, serif;
}
.form-part h3,
.form-part p {
  margin: 0;
}
.form-part h3 {
  color: #172554;
}
.form-part p {
  margin-top: 3px;
  color: #94a3b8;
  font-size: 12px;
}
.holding-form-part {
  background: #f5faf7;
  border-color: #d4e7dc;
}
.holding-form-part > header > span {
  background: #16735a;
}
.form-grid {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 22px;
}
.form-fields,
.two-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.form-fields {
  grid-template-columns: 1fr;
}
.admin-cover-picker > div {
  position: relative;
  display: grid;
  place-items: center;
  width: 120px;
  height: 168px;
  overflow: hidden;
  border-radius: 8px;
  background: #e8edf6;
  color: #64748b;
}
.admin-cover-picker img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.admin-cover-picker label {
  display: block;
  width: 120px;
  margin-top: 8px;
  padding: 7px 0;
  border: 1px solid #cfd8e7;
  border-radius: 7px;
  text-align: center;
  color: #3157a4;
  cursor: pointer;
}
.admin-cover-picker input {
  display: none;
}
.combined-form-actions {
  position: sticky;
  bottom: 0;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 0;
  background: #fff;
}
@media (max-width: 950px) {
  .admin-book-card {
    grid-template-columns: 76px 1fr 100px;
  }
  .holding-half {
    grid-column: 2;
    padding-top: 12px;
    border-top: 1px solid #e2e8f0;
  }
  .bibliographic-half {
    border-right: 0;
  }
  .admin-book-actions {
    grid-column: 3;
    grid-row: 1/3;
  }
}
@media (max-width: 650px) {
  .library-admin-tools {
    grid-template-columns: 1fr auto;
  }
  .library-admin-tools .el-button:last-child {
    grid-column: 1/3;
  }
  .admin-book-card {
    grid-template-columns: 60px 1fr;
  }
  .admin-book-card figure {
    width: 60px;
    height: 86px;
  }
  .holding-half,
  .admin-book-actions {
    grid-column: 1/3;
  }
  .admin-book-actions {
    grid-row: auto;
  }
  .form-grid,
  .two-fields {
    grid-template-columns: 1fr;
  }
}
</style>
