// Camera locations are illustrative links, not a claim about where the pictures were captured.
export const showcaseCameraCases = {
  'cam-01': 2, 'cam-02': 3, 'cam-03': 5, 'cam-04': 6,
  'cam-05': 4, 'cam-06': 8, 'cam-07': 1, 'cam-08': 7,
}

export function withShowcaseImage(camera, manifest = {}) {
  const caseId = showcaseCameraCases[camera.id]
  // A configured video always wins. Never silently replace a failed real stream with an example.
  if (!caseId || camera.streamUrl) return camera
  const result = manifest.cases?.find(item => Number(item.case) === caseId && item.status === 'done')
  return {
    ...camera, masks: [],
    exampleImageUrl: result?.overlay || `/examples/case${caseId}.png`,
    exampleOriginalUrl: `/examples/case${caseId}.png`,
    exampleCaseId: caseId,
    exampleJobId: result?.job_id || '',
    exampleLabel: result?.overlay ? '异常示例 · 本地模型重跑标注' : '异常示例 · 原图',
  }
}
