<template>
  <a-modal
    v-model:visible="visible"
    title="微信授权"
    :footer="false"
    :mask-closable="false"
    width="400px"
    @cancel="clearTimer"
  >
    <div class="qrcode-container">
      <div v-if="loading" class="loading">
        <a-spin size="large" />
        <p>正在获取二维码...</p>
      </div>
      <div v-else-if="qrcodeUrl" class="qrcode">
        <img :src="qrcodeUrl" alt="微信授权二维码" />
        <p>请使用微信扫码授权</p>
      </div>
      <div v-else class="error">
        <a-alert type="error" :message="errorMessage" />
        <a-button type="primary" @click="startAuth">重试</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { QRCode, checkQRCodeStatus } from '@/api/auth'
import { Message } from '@arco-design/web-vue'

const emit = defineEmits(['success', 'error'])

const visible = ref(false)
const loading = ref(false)
const qrcodeUrl = ref('')
const errorMessage = ref('')

let checkStatusTimer: number | null = null

const startAuth = async () => {
  try {
    visible.value = true
    loading.value = true
    errorMessage.value = ''
    
    // 获取二维码
    const res = await QRCode()
    qrcodeUrl.value = res?.code
    loading.value = false

    // 开始检查授权状态
        checkQRCodeStatus().then((statusRes) => {
          if (statusRes?.login_status) {
            clearTimer()
            Message.success('授权成功')
            emit('success', statusRes)
            visible.value = false
          }
        }).catch((err) => {
          console.error('检查二维码状态失败:', err)
          errorMessage.value = '授权失败，请重试'
           emit('error', err)
        })
  } catch (err) {
    loading.value = false
    errorMessage.value = '获取二维码失败，请重试'
    emit('error', err)
  }
}

const clearTimer = () => {
  if (checkStatusTimer) {
    clearInterval(checkStatusTimer)
    checkStatusTimer = null
  }
}

defineExpose({
  startAuth
})
</script>

<style scoped>
.qrcode-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.loading,
.qrcode,
.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.qrcode img {
  width: 200px;
  height: 200px;
}
</style>