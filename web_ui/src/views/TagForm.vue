<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTag, createTag, updateTag } from '@/api/tagManagement'
import type { Tag, TagCreate } from '@/types/tagManagement'
import { Message } from '@arco-design/web-vue'

const route = useRoute()
const router = useRouter()
const isEdit = ref(false)
const loading = ref(false)
const formLoading = ref(false)

const formModel = ref<TagCreate>({
  name: '',
  cover: null,
  intro: null,
  status: 1
})

const rules = {
  name: [{ required: true, message: '请输入标签名称' }]
}

const fetchTag = async (id: string) => {
  try {
    loading.value = true
    const res = await getTag(id)
    formModel.value = res.data
  } catch (error) {
    Message.error('获取标签详情失败')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  try {
    formLoading.value = true
    if (isEdit.value) {
      await updateTag(route.params.id as string, formModel.value)
      Message.success('更新成功')
    } else {
      await createTag(formModel.value)
      Message.success('创建成功')
    }
    router.push('/tags')
  } catch (error) {
    Message.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    formLoading.value = false
  }
}

onMounted(() => {
  if (route.params.id) {
    isEdit.value = true
    fetchTag(route.params.id as string)
  }
})
</script>

<template>
  <div class="tag-form">
    <a-page-header
      :title="isEdit ? '编辑标签' : '添加标签'"
      subtitle="标签信息"
      @back="router.go(-1)"
    />

    <a-card :loading="loading">
      <a-form
        :model="formModel"
        :rules="rules"
        layout="vertical"
        @submit="handleSubmit"
      >
        <a-form-item label="标签名称" field="name">
          <a-input v-model="formModel.name" placeholder="请输入标签名称" />
        </a-form-item>

        <a-form-item label="封面图" field="cover">
          <a-upload
            v-model:file-list="formModel.cover"
            action="/api/upload"
            :limit="1"
            list-type="picture-card"
          />
        </a-form-item>

        <a-form-item label="简介" field="intro">
          <a-textarea
            v-model="formModel.intro"
            placeholder="请输入标签简介"
            :auto-size="{ minRows: 3 }"
          />
        </a-form-item>

        <a-form-item label="状态" field="status">
          <a-switch
            v-model="formModel.status"
            :checked-value="1"
            :unchecked-value="0"
          />
        </a-form-item>

        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="formLoading">
              提交
            </a-button>
            <a-button @click="router.go(-1)">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<style scoped>
.tag-form {
  padding: 16px;
}
</style>