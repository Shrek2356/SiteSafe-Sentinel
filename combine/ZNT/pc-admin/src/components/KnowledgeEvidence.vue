<template>
  <details>
    <summary>规范检索证据（{{ references.length }} 条，适用性待人工核验）</summary>
    <p v-if="!references.length">{{ status === 'not_found' ? '本次未检索到可核验依据' : '未保存本次规范引用' }}，不代表无风险。</p>
    <article v-for="ref in references" :key="ref.chunk_id">
      <strong>{{ ref.title || ref.source_file }} · {{ ref.section }}</strong>
      <p>{{ ref.version || '版本未核验' }} · {{ ref.effective_status === 'active_as_checked' ? '核查当日有效，仍需确认适用性' : '效力状态：' + (ref.effective_status || '未核验') }}</p>
      <p v-if="ref.page_number">PDF页序：{{ ref.page_numbers?.length ? ref.page_numbers.join('、') : ref.page_number }}</p>
      <p style="white-space:pre-wrap">{{ ref.text }}</p>
      <a v-if="/^https?:\/\//i.test(ref.source_url || '')" :href="ref.source_url" target="_blank" rel="noopener noreferrer">官方/登记来源</a>
      <p style="overflow-wrap:anywhere">原文SHA256：{{ ref.document_sha256 || '旧记录未保存' }}；核查时间：{{ ref.checked_at || '未核验' }}</p>
    </article>
  </details>
</template>
<script setup>
defineProps({references:{type:Array,default:()=>[]}, status:{type:String,default:'not_retrieved'}})
</script>
