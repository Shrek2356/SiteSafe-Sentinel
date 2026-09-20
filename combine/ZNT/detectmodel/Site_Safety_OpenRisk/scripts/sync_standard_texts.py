"""Fetch public source text; fail on missing chapters before updating the corpus.

Maintenance-only dependencies: requests, beautifulsoup4. Not run during detection.
No OCR, LLM paraphrasing, or automated legal-validity certification.
"""
from pathlib import Path
from datetime import date
import hashlib
import json
import re
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'knowledge_base'
DOCS = ROOT / 'docs' / 'standards'
INDEX = 'https://gf.cabr-fire.com/m/list-2085.htm'
LAW = 'https://www.nea.gov.cn/2011-08/18/c_131057761.htm'
CHECKED = date.today().isoformat()


def fetch(url):
    last = None
    for _ in range(3):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except requests.RequestException as error:
            last = error
            time.sleep(1)
    raise last


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalized(text):
    return re.sub(r'\s+', '', text)


def main():
    catalog = json.loads((KB / 'source_catalog.json').read_text(encoding='utf-8'))
    if any(entry.get('source_status') == 'human_checked' for entry in catalog.values()):
        raise RuntimeError('知识库包含人工核验记录，请在独立暂存副本抓取并人工合并，禁止覆盖现有核验。')
    soup = BeautifulSoup(fetch(INDEX), 'html.parser')
    expected = {'1', '2', '4', '5', '6'} | {f'3.{i}' for i in range(1, 16)}
    links = {}
    for anchor in soup.select('a[href]'):
        title = anchor.get_text(' ', strip=True)
        number = title.split(' ')[0]
        if number in expected:
            links[number] = (title, urljoin(INDEX, anchor['href']))
    assert links.keys() == expected, f'Missing sections: {expected - links.keys()}'
    files, commentary, sections, all_bodies = {}, [], [], []
    for number in sorted(links, key=lambda n: tuple(map(int, n.split('.')))):
        title, url = links[number]
        html = fetch(url)
        soup = BeautifulSoup(html, 'html.parser')
        body = soup.select_one('#b_con')
        assert body is not None, url
        explanation = body.select_one('#explain')
        if explanation:
            commentary.append(f'## {title}\n\n来源：{url}\n\n' + explanation.get_text('\n', strip=True))
        for node in body.select('.twsm'):
            node.decompose()
        text = body.get_text('\n', strip=True)
        assert '条文说明' not in text, f'Commentary leaked: {url}'
        ids = re.findall(r'(?m)^(\d+\.\d+\.\d+)(?=\D|$)', text)
        assert ids and len(ids) == len(set(ids)), f'No/duplicate clauses: {url}'
        prefix = number if '.' in number else number + '.0'
        assert ids == [f'{prefix}.{i}' for i in range(1, len(ids) + 1)], (url, ids)
        filename = f'GB55034-2022-正文-{number}.md'
        document = f'# GB 55034-2022 {title}\n\n{text}\n'
        files[filename] = document
        all_bodies.append(text)
        catalog[filename] = dict(document_sha256=sha(document), title=f'GB 55034-2022 {title}（正文）',
            version='GB 55034-2022，2023-06-01施行', source_url=url,
            source_status='institution_text_structurally_checked', effective_status='unverified',
            content_kind='normative', checked_at=CHECKED,
            note='专业机构转录文本，章节/条款编号完整性已检查；不表示全部条款已对官方原件逐字核验或现场适用性已确认。')
        sections.append(dict(section=number, filename=filename, url=url, clauses=ids,
                             document_sha256=sha(document), source_html_sha256=sha(html)))
        print(number, len(ids), 'clauses', flush=True)

    # Compare every previously visually checked GB excerpt verbatim after whitespace normalization.
    old = (KB / 'GB55034-2022-核对节选.md').read_text(encoding='utf-8')
    corpus = normalized('\n'.join(all_bodies))
    for block in re.split(r'(?m)^## ', old)[1:]:
        body = block.split('\n', 1)[1].strip()
        assert normalized(body) in corpus, f'Previously checked excerpt differs: {block[:40]}'

    html = fetch(LAW)
    soup = BeautifulSoup(html, 'html.parser')
    last = soup.find(string=lambda text: text and '第七十一条' in text)
    assert last is not None
    container = last.find_parent('td')
    paragraphs = [p.get_text('', strip=True) for p in container.find_all('p')]
    start = next(i for i, p in enumerate(paragraphs) if p.startswith('第一章'))
    end = next(i for i, p in enumerate(paragraphs) if p.startswith('第七十一条'))
    law_text = '\n\n'.join(paragraphs[start:end+1])
    names = re.findall(r'(?m)^第([一二三四五六七八九十百]+)条', law_text)
    def chinese(i):
        digits = '零一二三四五六七八九'
        return digits[i] if i < 10 else (digits[i//10] if i >= 20 else '') + '十' + (digits[i%10] if i%10 else '')
    assert names == [chinese(i) for i in range(1, 72)]
    filename = '建设工程安全生产管理条例-全文.md'
    document = '# 建设工程安全生产管理条例\n\n' + law_text + '\n'
    files[filename] = document
    catalog[filename] = dict(document_sha256=sha(document), title='建设工程安全生产管理条例（全文71条）',
        version='国务院令第393号，2004-02-01施行', source_url=LAW,
        source_status='official_text_checked', effective_status='unverified', content_kind='normative', checked_at=CHECKED,
        note='官方网页直接提取第1—71条，编号连续性已检查；效力及适用范围应另行核查。网页前置日期未纳入条文。')
    for old_name in ['GB55034-2022-核对节选.md', '建设工程安全生产管理条例-核对节选.md']:
        catalog[old_name]['excluded'] = True
        catalog[old_name]['reason'] = '完整正文已入库，旧节选保留核对但不重复检索'
    DOCS.mkdir(parents=True, exist_ok=True)
    # Mechanical extraction outputs: exact source text, not authored standards.
    for name, text in files.items():
        (KB / name).write_text(text, encoding='utf-8', newline='\n')
    (DOCS / 'GB55034-2022-条文说明-非规范正文.md').write_text(
        '# GB 55034-2022 条文说明（辅助解释，不作为强制条款）\n\n' + '\n\n'.join(commentary) + '\n', encoding='utf-8', newline='\n')
    manifest = dict(checked_at=CHECKED, index_url=INDEX, sections=sections,
                    gb_clause_count=sum(len(s['clauses']) for s in sections), law_clause_count=len(names),
                    law_source_url=LAW, law_source_html_sha256=sha(html),
                    commentary_sections=len(commentary), gb_visual_comparison='4 previously checked clauses match',
                    limitation='GB全量逐字核对及法律有效性核验未完成；条文说明未进入规范索引。')
    (DOCS / 'TEXT_SOURCE_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (KB / 'source_catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps({k:v for k,v in manifest.items() if k != 'sections'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
