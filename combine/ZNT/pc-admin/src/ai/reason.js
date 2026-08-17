/**
 * 推理智能体对接位
 * -------------------------------------------------------
 * 【对接服务】规则引擎 / LLM 推理智能体
 * 【职责】风险定级、匹配规范条文、生成处置建议
 * 【修改入口】REASON_API_URL
 * -------------------------------------------------------
 */
import { USE_MOCK, mockDelay } from '@/utils/request'
import request from '@/utils/request'

export const REASON_API_URL = import.meta.env.VITE_REASON_API || '/ai/reason/analyze'

/**
 * 对检测结果进行推理分析
 *
 * 入参:
 * {
 *   risks: Array,              // 来自 vision.receiveRiskDetection
 *   context?: {
 *     cameraId, area, projectId, time
 *   }
 * }
 *
 * 出参:
 * {
 *   level: 'red'|'orange'|'yellow',
 *   title: string,
 *   regulation: string,        // 规范条文
 *   suggestion: string,        // 处置建议
 *   needWorkOrder: boolean
 * }
 */
export async function analyzeRisk(payload) {
  if (USE_MOCK) {
    const top = payload.risks?.[0]
    const level = top?.level || 'yellow'
    return mockDelay({
      level,
      title: top?.label || '未知风险',
      regulation: '《建筑施工安全检查标准》JGJ59-2011 相关条款（Mock）',
      suggestion:
        level === 'red'
          ? '立即停工并疏散相关区域人员，安全员15分钟内到场处置'
          : '责令现场整改，2小时内反馈结果',
      needWorkOrder: level !== 'yellow' || (top?.confidence || 0) > 0.8,
      source: 'reason-agent-mock',
    })
  }
  return request.post(REASON_API_URL, payload)
}
