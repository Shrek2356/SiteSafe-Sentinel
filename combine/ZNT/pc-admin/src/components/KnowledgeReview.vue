<template>
  <a-button type="link" @click="openPreview">解析预览 / 核验记录</a-button>
  <a-modal v-model:open="opened" title="规范原文与人工核验" width="900px" :footer="null">
    <a-spin :spinning="busy">
      <a-alert type="warning" show-icon message="这里记录管理员人工核验，不会自动认证规范有效或适用于现场；请先核对官方原文、修订公告和适用范围。" />
      <p>{{ filename }} · SHA256：{{ detail.document_sha256 }}</p>
      <a-button @click="download">下载当前原文件</a-button>
      <p v-for="(warning, i) in detail.warnings || []" :key="i">解析警告：{{ warning.error }}</p>
      <div style="max-height: 320px; overflow:auto; margin:16px 0">
        <article v-for="(chunk, i) in detail.chunks || []" :key="i">
          <strong>{{ chunk.section }} {{ chunk.page_numbers?.length ? `（PDF页序：${chunk.page_numbers.join('、')}）` : chunk.page_number ? `（PDF第${chunk.page_number}页）` : '' }}</strong>
          <p style="white-space:pre-wrap">{{ chunk.text }}</p>
        </article>
        <a-empty v-if="!detail.chunks?.length" description="没有可用解析片段，请检查文件或先进行OCR" />
      </div>
      <a-form layout="vertical">
        <a-form-item label="规范名称"><a-input v-model:value="form.title" /></a-form-item>
        <a-form-item label="编号与版本"><a-input v-model:value="form.version" /></a-form-item>
        <a-form-item label="官方来源网址"><a-input v-model:value="form.source_url" /></a-form-item>
        <a-form-item label="效力状态（人工核查结论）">
          <a-select v-model:value="form.effective_status" :options="statuses" />
        </a-form-item>
        <a-form-item label="下次复核日期"><input type="date" v-model="form.valid_until" /></a-form-item>
        <a-form-item label="核验依据、适用范围及修改原因"><a-textarea v-model:value="form.reason" :rows="3" /></a-form-item>
        <a-checkbox v-model:checked="form.excluded">排除出规范检索</a-checkbox>
        <p><a-button type="primary" :disabled="user.role !== 'admin' || !detail.document_sha256" :loading="busy" @click="save">提交人工核验（仅管理员）</a-button></p>
      </a-form>
      <h3>核验历史（旧引用快照不随此处修改）</h3>
      <p v-for="row in detail.history || []" :key="row.revision">{{ row.checked_at }} · {{ row.reviewed_by }} · {{ row.effective_status }} · {{ row.reason }}</p>
    </a-spin>
  </a-modal>
</template>
<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'
import { saveFile } from '@/utils/saveFile'
import { useUserStore } from '@/stores/user'
const user = useUserStore()
const props = defineProps({ filename: String })
const emit = defineEmits(['updated'])
const opened = ref(false), busy = ref(false), detail = ref({}), form = ref({})
const statuses = [{value:'unverified',label:'待核验'}, {value:'active_as_checked',label:'核查当日有效'}, {value:'repealed',label:'已废止'}, {value:'superseded',label:'已被替代'}]
async function openPreview() {
  opened.value = true; busy.value = true
  try {
    detail.value = (await request.get('/knowledge/preview', {params:{filename:props.filename}})).data
    form.value = {title:'', version:'', source_url:'', effective_status:'unverified', valid_until:'', reason:'', ...detail.value.metadata, excluded:detail.value.excluded}
  } catch (e) { message.error(e.response?.data?.detail || '规范预览失败') }
  finally { busy.value = false }
}
async function save() {
  busy.value = true
  try {
    await request.post('/knowledge/review', {...form.value, filename:props.filename, document_sha256:detail.value.document_sha256, revision:detail.value.revision})
    message.success('人工核验已留痕，仅影响之后的新检索'); emit('updated'); await openPreview()
  } catch (e) { message.error(e.response?.data?.detail || '保存失败，请检查权限及必填信息') }
  finally { busy.value = false }
}
async function download() {
  try { const res = await request.get('/knowledge/source', {params:{filename:props.filename}, responseType:'blob'}); await saveFile(res.data, props.filename) }
  catch (e) { message.error('原文件下载失败') }
}
</script>
