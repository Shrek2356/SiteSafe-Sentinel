<template>
  <div class="page-card">
    <div class="page-title">Agent 协同与学习中心</div>
    <a-alert type="info" show-icon message="这里承接模型不确定结果的人工裁决、复盘学习建议、通知与安全交底；所有操作写入业务数据库。" />
    <a-tabs v-model:activeKey="tab" style="margin-top: 14px">
      <a-tab-pane key="review" tab="人工复核">
        <a-table :columns="reviewColumns" :data-source="confirmations" row-key="request_id" :loading="loading">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'confidence'">{{ Math.round((record.model_confidence || 0) * 100) }}%</template>
            <template v-if="column.key === 'status'"><a-tag :color="record.status === 'pending' ? 'orange' : 'green'">{{ statusText(record.status) }}</a-tag></template>
            <template v-if="column.key === 'action'">
              <a-space v-if="record.status === 'pending' && canReview">
                <a-button size="small" type="primary" @click="openReview(record, 'confirmed')">确认异常</a-button>
                <a-button size="small" danger @click="openReview(record, 'rejected')">排除异常</a-button>
              </a-space>
              <span v-else>—</span>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="learning" tab="复盘学习建议">
        <a-alert type="warning" show-icon message="建议只在管理员批准后写入阈值覆盖配置；模型不会自行修改生产规则。" style="margin-bottom: 12px" />
        <a-table :columns="proposalColumns" :data-source="proposals" row-key="proposal_id" :loading="loading">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'threshold'">{{ record.proposed_min_verified_confidence }}</template>
            <template v-if="column.key === 'status'"><a-tag>{{ statusText(record.status) }}</a-tag></template>
            <template v-if="column.key === 'action'">
              <a-space v-if="record.status === 'pending' && isAdmin">
                <a-button size="small" type="primary" @click="reviewProposal(record, 'approve')">批准</a-button>
                <a-button size="small" @click="reviewProposal(record, 'reject')">拒绝</a-button>
              </a-space>
              <span v-else>—</span>
            </template>
          </template>
        </a-table>
        <a-collapse style="margin-top: 12px"><a-collapse-panel key="1" header="当前生效阈值覆盖"><pre>{{ JSON.stringify(overrides, null, 2) }}</pre></a-collapse-panel></a-collapse>
      </a-tab-pane>

      <a-tab-pane key="briefing" tab="通知与交底">
        <a-space style="margin-bottom: 12px"><a-button @click="loadAll">刷新</a-button><a-button @click="downloadBriefing">下载交底 Markdown</a-button></a-space>
        <a-row :gutter="14">
          <a-col :xs="24" :xl="12"><a-card title="安全交底"><pre class="briefing">{{ briefing || '暂无内容' }}</pre></a-card></a-col>
          <a-col :xs="24" :xl="12"><a-card title="通知记录"><a-list :data-source="notifications" bordered><template #renderItem="{ item }"><a-list-item><a-list-item-meta :title="item.title || item.risk_name_zh || '风险通知'" :description="item.message || item.content || JSON.stringify(item)" /></a-list-item></template></a-list></a-card></a-col>
        </a-row>
      </a-tab-pane>

      <a-tab-pane v-if="isAdmin" key="system" tab="用户与备份">
        <a-space style="margin-bottom: 12px"><a-button type="primary" @click="userOpen = true">新增用户</a-button><a-button @click="backup">立即备份业务库</a-button></a-space>
        <a-table :columns="userColumns" :data-source="users" row-key="username" :pagination="false">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'role'"><a-select :value="record.role" style="width: 150px" @change="(role) => changeRole(record, role)"><a-select-option value="admin">管理员</a-select-option><a-select-option value="safety_officer">安全员</a-select-option><a-select-option value="viewer">只读总监</a-select-option></a-select></template>
            <template v-if="column.key === 'action'"><a-button type="link" @click="resetPassword(record)">重置密码</a-button></template>
          </template>
        </a-table>
      </a-tab-pane>
    </a-tabs>

    <a-modal v-model:open="reviewOpen" title="提交人工判断" @ok="submitReview"><a-form layout="vertical"><a-form-item label="模型判断"><a-textarea :value="reviewTarget?.model_judgment || reviewTarget?.reason || reviewTarget?.risk_name_zh || reviewTarget?.risk_id" :rows="2" disabled /></a-form-item><a-form-item v-if="reviewTarget?.visible_evidence?.length" label="支持证据"><a-alert type="success" :message="reviewTarget.visible_evidence.join('；')" /></a-form-item><a-form-item v-if="reviewTarget?.counter_evidence?.length" label="反证/不确定项"><a-alert type="warning" :message="reviewTarget.counter_evidence.join('；')" /></a-form-item><a-form-item label="安全人员备注"><a-textarea v-model:value="reviewComment" :rows="3" placeholder="填写可见证据或排除依据" /></a-form-item></a-form></a-modal>
    <a-modal v-model:open="userOpen" title="新增平台用户" @ok="addUser"><a-form layout="vertical"><a-form-item label="用户名"><a-input v-model:value="newUser.username" /></a-form-item><a-form-item label="初始密码（至少6位）"><a-input-password v-model:value="newUser.password" /></a-form-item><a-form-item label="角色"><a-select v-model:value="newUser.role"><a-select-option value="safety_officer">安全员</a-select-option><a-select-option value="viewer">只读总监</a-select-option><a-select-option value="admin">管理员</a-select-option></a-select></a-form-item></a-form></a-modal>
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref } from 'vue'
import { Modal, message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { createBackup, createUser, decideConfirmation, decideProposal, fetchBriefing, fetchConfirmations, fetchNotifications, fetchOverrides, fetchProposals, fetchUsers, updateUserPassword, updateUserRole } from '@/api/agentCenter'

const store = useUserStore()
const isAdmin = computed(() => store.role === 'admin')
const canReview = computed(() => ['admin', 'safety'].includes(store.role))
const tab = ref('review'), loading = ref(false)
const confirmations = ref([]), proposals = ref([]), overrides = ref({}), notifications = ref([]), briefing = ref(''), users = ref([])
const reviewOpen = ref(false), reviewTarget = ref(null), reviewVerdict = ref('confirmed'), reviewComment = ref('')
const userOpen = ref(false), newUser = reactive({ username: '', password: '', role: 'safety_officer' })
const reviewColumns = [{ title: '风险', dataIndex: 'risk_name_zh', key: 'risk_name_zh' }, { title: '模型疑问/判断', dataIndex: 'model_judgment', key: 'model_judgment' }, { title: '转人工原因', dataIndex: 'reason', key: 'reason' }, { title: '置信度', key: 'confidence', width: 100 }, { title: '状态', key: 'status', width: 100 }, { title: '操作', key: 'action', width: 180 }]
const proposalColumns = [{ title: '风险类型', dataIndex: 'risk_id' }, { title: '样本数', dataIndex: 'sample_count' }, { title: '建议阈值', key: 'threshold' }, { title: '原因', dataIndex: 'reason' }, { title: '状态', key: 'status' }, { title: '操作', key: 'action' }]
const userColumns = [{ title: '用户名', dataIndex: 'username' }, { title: '角色', key: 'role' }, { title: '操作', key: 'action' }]
const statusText = (s) => ({ pending: '待处理', confirmed: '已确认', rejected: '已排除', approved: '已批准' }[s] || s)

async function loadAll() {
  loading.value = true
  try {
    const base = await Promise.all([fetchConfirmations(), fetchProposals(), fetchOverrides(), fetchNotifications(), fetchBriefing()])
    confirmations.value = base[0].data; proposals.value = base[1].data; overrides.value = base[2].data; notifications.value = base[3].data; briefing.value = base[4].data.markdown
    if (isAdmin.value) users.value = (await fetchUsers()).data
  } finally { loading.value = false }
}
function openReview(record, verdict) { reviewTarget.value = record; reviewVerdict.value = verdict; reviewComment.value = ''; reviewOpen.value = true }
async function submitReview() { await decideConfirmation(reviewTarget.value.request_id, { verdict: reviewVerdict.value, comment: reviewComment.value }); message.success('人工判断已回写并进入复盘链路'); reviewOpen.value = false; await loadAll() }
async function reviewProposal(record, decision) { await decideProposal(record.proposal_id, { decision, note: '由管理端人工审批' }); message.success('学习建议已处理'); await loadAll() }
async function addUser() { await createUser(newUser); message.success('用户已创建'); userOpen.value = false; Object.assign(newUser, { username: '', password: '', role: 'safety_officer' }); await loadAll() }
async function changeRole(record, role) { await updateUserRole(record.username, role); message.success('角色已更新'); await loadAll() }
function resetPassword(record) { let password = ''; Modal.confirm({ title: `重置 ${record.username} 的密码`, content: () => h('input', { class: 'ant-input', type: 'password', placeholder: '至少6位', onInput: (e) => { password = e.target.value } }), onOk: async () => { await updateUserPassword(record.username, password); message.success('密码已更新') } }) }
async function backup() { const res = await createBackup(); message.success(`备份完成：${res.data.backup}`) }
function downloadBriefing() { const blob = new Blob([briefing.value], { type: 'text/markdown;charset=utf-8' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '安全交底.md'; a.click(); URL.revokeObjectURL(a.href) }
onMounted(loadAll)
</script>

<style scoped>
.briefing { white-space: pre-wrap; max-height: 520px; overflow: auto; color: var(--text-primary); font-family: inherit; }
pre { white-space: pre-wrap; color: var(--text-primary); }
</style>
