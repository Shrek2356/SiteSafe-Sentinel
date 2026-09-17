<template>
  <details style="margin:12px 0; overflow-wrap:anywhere">
    <summary>查看规范证据 · 人工{{ {confirmed:'已确认', rejected:'已驳回'}[record.humanReviewStatus] || '待确认' }}</summary>
    <p v-if="!record.knowledgeReferences?.length">未保存本次可核验依据，不代表无风险。</p>
    <article v-for="ref in record.knowledgeReferences || []" :key="ref.chunk_id">
      <strong>{{ ref.title || ref.source_file }} · {{ ref.section }}</strong>
      <p>{{ ref.version || '版本未核验' }} · {{ ref.page_numbers?.length ? `PDF页序：${ref.page_numbers.join('、')}` : ref.page_number ? `PDF第${ref.page_number}页` : '' }} · 适用性待核验</p>
      <p>效力记录：{{ ref.effective_status || 'unverified' }}；核查：{{ ref.checked_at || '未核验' }}</p>
      <p style="white-space:pre-wrap">{{ ref.text }}</p>
      <a v-if="/^https?:\/\//i.test(ref.source_url || '')" :href="ref.source_url" target="_blank" rel="noopener noreferrer">查看登记来源</a>
    </article>
  </details>
</template>
<script setup>
defineProps({record:{type:Object,default:()=>({})}})
</script>
