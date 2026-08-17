/**
 * 实时检测结果 → 检测结果汇总（本地汇总）
 * 与工单同步并列：一次检测完成后可同时进入「结果汇总」与「工单处置」
 */
import { notifyModules } from './moduleBus'

const STORAGE_KEY = 'znt_detect_results'

function media(url = '') {
  if (!url) return ''
  if (/^https?:\/\//i.test(url) || url.startsWith('blob:') || url.startsWith('data:')) return url
  if (url.startsWith('/detect-api/')) return url
  if (url.startsWith('/api/detect/')) return `/detect-api${url}`
  return url
}

export function loadDetectResultCases() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const list = raw ? JSON.parse(raw) : []
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

function saveDetectResultCases(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

/**
 * 将完成的检测任务写入结果汇总（幂等：同一 job_id 覆盖）
 */
export function syncDetectJobToResults(job) {
  if (!job || job.status !== 'done') return null
  const result = job.result || {}
  const risks = result.risks || []
  const top = risks[0] || {}
  const conf = Number(top.confidence ?? result.confidence ?? 0.7)
  const needReview = !!(top.manual_review || result.manual_review || conf < 0.85)
  const autoConfirm = top.verified !== false && !needReview
  let status = 'confirmed'
  if (needReview && conf >= 0.6) status = 'partial'
  else if (needReview) status = 'review'
  else status = 'confirmed'

  const overlay = media(result.overlays?.[0] || top.overlay || '')
  const original = media(result.input_image || '')
  const mask = media(result.masks?.[0] || top.mask || overlay)
  const caseId = `live-${String(job.job_id || '').replace(/[^A-Za-z0-9_-]/g, '').slice(-24) || Date.now()}`
  const presentationAsset = Boolean(job.mock || job.profile === 'demo')

  const item = {
    id: caseId,
    expected: top.name || '实时检测风险',
    result: result.report_summary || top.description || (result.overall_has_anomaly ? '发现风险' : '未发现需确认风险'),
    confidence: conf,
    autoConfirm,
    humanReview: needReview,
    status,
    analysis: top.description || result.report_summary || '来自实时检测任务',
    suggestion: (top.suggestions && top.suggestions[0]) || '请结合标注图复核并进入工单处置',
    cover: overlay || original,
    images: { original, overlay: overlay || original, mask },
    detectJobId: job.job_id,
    profile: job.profile,
    source: 'realtime-detect',
    live: true,
    presentationAsset,
    sourceType: presentationAsset ? 'demo-run' : 'pending-sync',
    createTime: job.finished_at || job.created_at || new Date().toISOString(),
    riskCount: result.risk_count ?? risks.length,
  }

  const list = loadDetectResultCases().filter((c) => c.detectJobId !== job.job_id && c.id !== caseId)
  list.unshift(item)
  saveDetectResultCases(list.slice(0, 50))
  notifyModules({ type: 'detect-results', jobId: job.job_id, caseId })
  return item
}

export function getDetectResultCaseByJob(jobId) {
  if (!jobId) return null
  return loadDetectResultCases().find((c) => c.detectJobId === jobId || c.id === `live-${jobId}`) || null
}
