/** Only explicitly identified presentation points may use the GLB illustration coordinates. */
const anchors = {
  '塔吊A区': [6, 40, -13], '基坑B区': [0, 2, 9],
  '材料堆场': [30, 5, -14], '脚手架C区': [-7, 23, -15],
  '钢筋加工棚': [-26, 6, -1], '出入口岗亭': [-26, 5, 40],
}
export function sceneMarkers(points, demo) {
  if (!demo) return []
  return points.filter(p => Object.hasOwn(anchors, p.name))
    .map(p => ({ ...p, position: [...anchors[p.name]], source: 'presentation' }))
}
