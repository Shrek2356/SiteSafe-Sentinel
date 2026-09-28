<template>
  <section class="knowledge-evidence">
    <a-button @click="open=true">图像与规范证据 · {{ references.length }} 条</a-button>
    <p v-if="!references.length">{{ missingText }}，不代表无风险。</p>
    <a-modal v-model:open="open" title="图像与规范证据 · 保存时的引用快照" :footer="null" width="1100px">
      <a-alert type="info" show-icon message="引用相关不等于违规已确认；请核对适用条件与现场事实。此处不重新检索，不补写旧记录时间。" />
      <div class="evidence-layout">
        <div class="evidence-image"><h3>{{ imageTitle || '现场图像' }}</h3><img v-if="image" :src="image" alt="当前记录的现场图像或标注图" /><p v-else>该记录未保存可访问图像。</p><p>模型描述、掩码与规范条文均供人工判断，不替代现场核验。</p></div>
        <div class="evidence-text">
          <p v-if="!references.length">{{ missingText }}，请转人工查证。</p>
          <article v-for="(ref,index) in references" :key="ref.chunk_id || index">
            <h3>{{ index+1 }}. {{ ref.title || ref.source_file || '来源未记录' }} · {{ ref.section || '章节未记录' }}</h3>
            <p v-if="ref.risk_type || ref.risk_id">关联风险：{{ ref.risk_type || ref.risk_id }}</p>
            <p>{{ ref.version || '版本未核验' }} · {{ ref.effective_status === 'active_as_checked' ? '核查当日有效，仍需确认适用性' : '效力状态：' + (ref.effective_status || '未核验') }}</p>
            <p v-if="ref.page_number || ref.page_numbers?.length">PDF页序：{{ ref.page_numbers?.length ? ref.page_numbers.join('、') : ref.page_number }}</p>
            <blockquote>{{ ref.text || '未保存条文原文，请查阅来源。' }}</blockquote>
            <a v-if="/^https?:\/\//i.test(ref.source_url || '')" :href="ref.source_url" target="_blank" rel="noopener noreferrer">打开官方 / 登记来源 ↗</a>
            <details><summary>来源校验信息</summary><p>文件：{{ ref.source_file || '未记录' }}</p><p>原文 SHA256：{{ ref.document_sha256 || '旧记录未保存' }}</p><p>来源核查时间：{{ ref.checked_at || '未核验' }}（不是本次检索时间）</p></details>
          </article>
        </div>
      </div>
    </a-modal>
  </section>
</template>
<script setup>
import { computed,ref } from 'vue'
const props=defineProps({references:{type:Array,default:()=>[]},status:{type:String,default:'not_retrieved'},image:{type:String,default:''},imageTitle:{type:String,default:''}})
const open=ref(false)
const missingText=computed(()=>props.status==='not_found'?'本次未检索到可核验依据':'未保存本次规范引用')
</script>
<style scoped>
.knowledge-evidence{margin:12px 0}.knowledge-evidence>p{font-size:12px;color:var(--text-secondary)}.evidence-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);gap:22px;margin-top:18px}.evidence-image img{width:100%;max-height:520px;object-fit:contain;background:var(--media-bg);border-radius:8px}.evidence-image p{font-size:13px;color:var(--text-secondary)}.evidence-text{max-height:65vh;overflow:auto;padding-right:10px}.evidence-text article{border:1px solid var(--border-color);border-radius:8px;padding:14px;margin-bottom:12px}.evidence-text h3,.evidence-image h3{font-size:16px;overflow-wrap:anywhere}.evidence-text p{font-size:13px;overflow-wrap:anywhere}.evidence-text blockquote{white-space:pre-wrap;margin:12px 0;padding:12px;border-left:3px solid var(--primary);background:var(--surface-2);line-height:1.8}.evidence-text summary{cursor:pointer;color:var(--text-secondary);margin-top:12px}@media(max-width:760px){.evidence-layout{grid-template-columns:1fr}.evidence-text{max-height:none}.evidence-image img{max-height:300px}}
</style>
