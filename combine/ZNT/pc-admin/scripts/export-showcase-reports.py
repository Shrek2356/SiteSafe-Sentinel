"""Export reviewed example reports without machine paths, raw prompts or a business database."""
import argparse
import html
import json
from pathlib import Path

def export(batch, destination):
    for case in range(1, 9):
        report = json.loads((batch / f'case{case}' / 'final_report.json').read_text(encoding='utf-8'))
        esc = lambda v: html.escape(str(v))
        sections = []
        for risk in report.get('risks', []):
            sections.append('<section><h2>' + esc(risk.get('risk_name_zh', '风险候选')) + '</h2><p>'
                + ('机器判断：有证据支持' if risk.get('verified') else '机器判断：待复核')
                + ' · 最终判断由安全员完成</p><p>' + esc(risk.get('summary', '')) + '</p>')
            for key, title in [('evidence','支持证据'),('counter_evidence','反证'),('uncertainties','疑点与局限')]:
                sections.append('<h3>'+title+'</h3><ul>'+''.join('<li>'+esc(v)+'</li>' for v in risk.get(key, []))+'</ul>')
            sections.append('</section>')
        content = ''.join(sections) or '<section><h2>本次未检出异常</h2><p>不等于确认现场安全；不以旧版正例标注替换本次结果。</p></section>'
        page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>筑安智巡 · 示例报告</title><style>body{max-width:1000px;margin:32px auto;padding:20px;background:#101f38;color:#edf3fc;font:17px/1.8 sans-serif}section{padding:20px;margin:20px 0;background:#192c48;border-radius:12px}img{max-width:100%}a{color:#a8d4ff}</style><h1>示例 '+str(case)+' · 本地重跑报告快照</h1><p>2026-09-27 · YOLO / 本地 Qwen / SAM3 · 模板报告，无云端调用。静态示例，非实时视频；报告不是人工结论。</p><p>'+esc(report.get('executive_summary',''))+'</p><img src="../../examples/case'+str(case)+'.png" alt="原图">'+content+'<p>来源：本地八图重跑。仅发布结构化证据；不包含原始推理日志、开发机路径或数据库。</p></html>'
        # reports live at /showcase/latest; originals at /examples
        page = page.replace('../../examples/', '/examples/')
        (destination / f'case{case}_report.html').write_text(page, encoding='utf-8')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('batch', type=Path)
    p.add_argument('destination', type=Path)
    a = p.parse_args()
    export(a.batch, a.destination)
