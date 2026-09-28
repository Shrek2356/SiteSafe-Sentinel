/** Only explicitly identified presentation points may use the schematic coordinates. */
const anchors = {
  '塔吊A区': [1, 59, -30], '基坑B区': [26, 6, 12],
  '材料堆场': [42, 7, -52], '脚手架C区': [-34, 48, -45],
  '钢筋加工棚': [-36, 15, 18], '出入口岗亭': [-68, 11, 54],
}
export function sceneMarkers(points, demo) {
  if (!demo) return []
  return points.filter(p => Object.hasOwn(anchors, p.name))
    .map(p => ({ ...p, position: [...anchors[p.name]], source: 'presentation' }))
}
