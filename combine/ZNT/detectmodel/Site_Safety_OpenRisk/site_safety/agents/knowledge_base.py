"""条款级RAG知识库：把任意安全规程文档扔进目录即可被检索。

用法：把 .md / .txt / .pdf / .docx 文件放入 knowledge_base/ 目录，
系统按标题与条款编号切块，采用本地TF-IDF字符检索，不调用大模型。
source_catalog.json 保存与文件哈希绑定的来源核验信息；无核验的上传文件
仅作为未核验参考。检索相似度不代表条文适用性或法律效力。
文件增删改后自动重建索引（按目录指纹判断）。
"""
from __future__ import annotations

import re
import hashlib
import json
import os
import uuid
from datetime import date, datetime, timezone
import tempfile
import threading
from functools import wraps
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

# 条款切分锚点：markdown标题 / "第x条|章|节" / "1.2.3"式编号
_CLAUSE_PATTERN = re.compile(
    r"^(#{1,6}\s+.+|第[一二三四五六七八九十百\d]+[条章节].*|\d+(?:\.\d+)+\s*.+)$",
    re.MULTILINE,
)
_MAX_CHUNK_CHARS = 600
_MIN_CHUNK_CHARS = 10


def _locked(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapped


@dataclass
class KnowledgeChunk:
    chunk_id: str
    source_file: str
    section: str
    text: str
    metadata: dict = field(default_factory=dict)
    page_number: Optional[int] = None


def _read_pages(path: Path) -> List[Tuple[Optional[int], str]]:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return [(None, path.read_text(encoding="utf-8-sig"))]
    if suffix == ".pdf":
        from pypdf import PdfReader

        pages = [(i + 1, page.extract_text() or "") for i, page in enumerate(PdfReader(str(path)).pages)]
        if any(text.count('\x00') > max(2, len(text) * 0.05) for _, text in pages):
            raise ValueError("PDF文本层含大量乱码，需OCR并人工核对后导入；不能作为有效规范文本")
        return pages
    if suffix == ".docx":
        import docx

        from docx.text.paragraph import Paragraph
        from docx.table import Table
        document = docx.Document(str(path))
        blocks = []
        for node in document.element.body.iterchildren():
            if node.tag.endswith('}p'):
                blocks.append(Paragraph(node, document).text)
            elif node.tag.endswith('}tbl'):
                blocks.extend(' | '.join(cell.text for cell in row.cells) for row in Table(node, document).rows)
        return [(None, '\n'.join(blocks))]
    return []


def _read_document(path: Path) -> str:
    return '\n'.join(text for _, text in _read_pages(path))


def _split_clauses(text: str) -> List[Tuple[str, str]]:
    """按标题/条款编号切块，返回[(section标题, 正文)]；超长块再按空行细分。"""
    matches = list(_CLAUSE_PATTERN.finditer(text))
    blocks: List[Tuple[str, str]] = []
    if not matches:
        blocks = [("正文", text)]
    else:
        if matches[0].start() > 0:
            blocks.append(("前言", text[: matches[0].start()]))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = match.group(0).lstrip("# ").strip()
            blocks.append((section, text[match.end():end]))
    chunks: List[Tuple[str, str]] = []
    for section, body in blocks:
        body = body.strip()
        content = f"{section}\n{body}" if body else section
        if len(content) < _MIN_CHUNK_CHARS:
            continue
        if len(content) <= _MAX_CHUNK_CHARS:
            chunks.append((section, content))
        else:  # 超长条款按空行二次切分
            part = ""
            for paragraph in re.split(r"\n\s*\n", content):
                if len(part) + len(paragraph) > _MAX_CHUNK_CHARS and part:
                    chunks.append((section, part.strip()))
                    part = ""
                part += paragraph + "\n\n"
            if part.strip():
                chunks.append((section, part.strip()))
    return chunks


class KnowledgeBase:
    def __init__(self, kb_dir: str | Path) -> None:
        self._lock = threading.RLock()
        self.kb_dir = Path(kb_dir)
        self.chunks: List[KnowledgeChunk] = []
        self._fingerprint: Optional[tuple] = None
        self._retriever = None
        self.parse_errors: List[dict] = []
        self.refresh()

    def _catalog(self) -> dict:
        path = self.kb_dir / 'source_catalog.json'
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            return data if isinstance(data, dict) else {}
        except (ValueError, OSError):
            return {}

    def source_path(self, filename: str) -> Path:
        if Path(filename).name != filename or filename in {'', '.', '..'} or '\\' in filename:
            raise ValueError('文件名无效')
        path = (self.kb_dir / filename).resolve()
        if path.parent != self.kb_dir.resolve() or not path.is_file() or path.suffix.lower() not in {'.md', '.txt', '.pdf', '.docx'}:
            raise ValueError('规范文件不存在或不允许访问')
        return path

    @_locked
    def preview(self, filename: str) -> dict:
        path = self.source_path(filename)
        self.refresh()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entry = self._catalog().get(filename, {})
        bound = entry if entry.get('document_sha256') == digest else {}
        chunks = [{'chunk_id': c.chunk_id, 'section': c.section, 'text': c.text,
                   'page_number': c.page_number} for c in self.chunks if c.source_file == filename]
        if entry.get('excluded'):
            try:
                chunks = [{'section': section, 'text': text, 'page_number': page}
                          for page, content in _read_pages(path) for section, text in _split_clauses(content)]
            except Exception:
                chunks = []
        return {'source_file': filename, 'document_sha256': digest,
                'revision': entry.get('revision', ''), 'metadata': bound,
                'excluded': bool(entry.get('excluded')),
                'chunks': chunks,
                'warnings': [e for e in self.parse_errors if e['source_file'] == filename],
                'history': self.audit_history(filename)}

    def audit_history(self, filename: str) -> list:
        folder = self.kb_dir / '.history' / 'reviews'
        return sorted([json.loads(p.read_text(encoding='utf-8')) for p in folder.glob('*.json')
                       if json.loads(p.read_text(encoding='utf-8')).get('source_file') == filename],
                      key=lambda row: row['checked_at'], reverse=True) if folder.exists() else []

    @_locked
    def review_source(self, filename: str, payload: dict, reviewer: str) -> dict:
        """Record an authenticated human attestation, not automatic legal validation."""
        current = self.preview(filename)
        if payload.get('document_sha256') != current['document_sha256'] or payload.get('revision', '') != current['revision']:
            raise ValueError('文档或核验记录已变化，请重新预览后提交')
        required = ('title', 'version', 'source_url', 'reason', 'valid_until')
        if any(not isinstance(payload.get(k), str) or not payload[k].strip() for k in required):
            raise ValueError('请填写标题、版本、官方出处、核验理由和复核日期')
        from urllib.parse import urlparse
        url = urlparse(payload['source_url'])
        if url.scheme not in {'http', 'https'} or not url.netloc:
            raise ValueError('来源必须是http(s)网址')
        expiry = date.fromisoformat(payload['valid_until'])
        if expiry < date.today():
            raise ValueError('复核日期不能早于今天')
        status = payload.get('effective_status', 'unverified')
        if status not in {'unverified', 'active_as_checked', 'repealed', 'superseded'}:
            raise ValueError('效力状态无效')
        if not current['chunks'] and not payload.get('excluded', False):
            raise ValueError('无可用解析文本，不能批准为检索来源')
        entry = {k: payload[k].strip() for k in required}
        entry.update(document_sha256=current['document_sha256'], source_status='human_checked',
                     effective_status=status, excluded=bool(payload.get('excluded', False)),
                     checked_at=datetime.now(timezone.utc).isoformat(), reviewed_by=reviewer,
                     revision=uuid.uuid4().hex)
        self._archive(self.source_path(filename))
        archive = self.kb_dir / '.history' / 'reviews'
        archive.mkdir(parents=True, exist_ok=True)
        with (archive / f"{entry['revision']}.json").open('x', encoding='utf-8') as handle:
            json.dump({'source_file': filename, **entry, 'previous': current['metadata']}, handle, ensure_ascii=False, indent=2)
        catalog = self._catalog()
        catalog[filename] = entry
        temporary = self.kb_dir / f'.catalog-{uuid.uuid4().hex}.tmp'
        temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, self.kb_dir / 'source_catalog.json')
        self.refresh(force=True)
        return self.preview(filename)

    def _archive(self, path: Path) -> None:
        """Keep immutable source bytes, even across same-name replacement/deletion."""
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        archive = self.kb_dir / '.history' / digest
        archive.mkdir(parents=True, exist_ok=True)
        target = archive / path.name
        if not target.exists():
            with target.open('xb') as handle:
                handle.write(content)

    @_locked
    def import_document(self, filename: str, content: bytes) -> int:
        """Validate staged content before atomically replacing an existing document."""
        if Path(filename).name != filename or Path(filename).suffix.lower() not in {".txt", ".md", ".pdf", ".docx"}:
            raise ValueError("规范文件名或格式无效")
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        target = self.kb_dir / filename
        previous = target.read_bytes() if target.is_file() else None
        with tempfile.TemporaryDirectory(prefix=".import-", dir=self.kb_dir) as staging:
            candidate = Path(staging) / filename
            candidate.write_bytes(content)
            if not _split_clauses(_read_document(candidate)):
                raise ValueError("文件未解析出有效文本，请检查PDF是否为扫描件或文档内容是否为空；旧规范保持不变")
            if target.exists():
                self._archive(target)
            candidate.replace(target)
            try:
                self.refresh(force=True)
                self.prepare_index()
                self._archive(target)
            except Exception:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    candidate.write_bytes(previous)
                    candidate.replace(target)
                self.refresh(force=True)
                self.prepare_index()
                raise
        return sum(c.source_file == filename for c in self.chunks)

    @_locked
    def delete_document(self, filename: str) -> None:
        if Path(filename).name != filename:
            raise ValueError("文件名无效")
        self._archive(self.kb_dir / filename)
        (self.kb_dir / filename).unlink()
        self.refresh(force=True)
        self.prepare_index()

    def _current_fingerprint(self) -> tuple:
        if not self.kb_dir.is_dir():
            return ()
        return (date.today().isoformat(),) + tuple(
            sorted(
                (p.name, p.stat().st_mtime_ns, p.stat().st_size)
                for p in self.kb_dir.iterdir()
                if p.is_file() and (p.suffix.lower() in {".md", ".txt", ".pdf", ".docx"} or p.name == 'source_catalog.json')
            )
        )

    @_locked
    def refresh(self, *, force: bool = False) -> bool:
        """目录有变化时重建索引；返回是否重建。"""
        fingerprint = self._current_fingerprint()
        if not force and fingerprint == self._fingerprint:
            return False
        self._fingerprint = fingerprint
        self.chunks = []
        self.parse_errors = []
        catalog = self._catalog()
        if self.kb_dir.is_dir():
            for path in sorted(self.kb_dir.iterdir()):
                if path.suffix.lower() not in {".md", ".txt", ".pdf", ".docx"}:
                    continue
                entry = catalog.get(path.name, {})
                if entry.get('excluded'):
                    continue
                try:
                    pages = _read_pages(path)
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                except Exception as exc:
                    self.parse_errors.append({'source_file': path.name, 'error': str(exc)})
                    continue
                metadata = {'document_sha256': digest, 'source_status': 'unverified', 'effective_status': 'unverified'}
                if entry.get('document_sha256') == digest:
                    metadata.update({k: entry[k] for k in ('source_url', 'title', 'version', 'source_status', 'effective_status', 'checked_at', 'reviewed_by', 'valid_until', 'revision') if k in entry})
                    if entry.get('valid_until') and entry['valid_until'] < date.today().isoformat():
                        metadata['effective_status'] = 'review_due'
                for page_number, text in pages:
                    if not text.strip():
                        self.parse_errors.append({'source_file': path.name, 'page_number': page_number, 'error': '无可提取文本，请检查扫描页/OCR'})
                    for index, (section, content) in enumerate(_split_clauses(text)):
                        chunk_digest = hashlib.sha256(f'{path.name}|{digest}|{page_number}|{index}|{content}'.encode()).hexdigest()[:24]
                        self.chunks.append(KnowledgeChunk(
                            chunk_id=f'KB-{chunk_digest}', source_file=path.name,
                            section=section, text=content, metadata=dict(metadata), page_number=page_number,
                        ))
        self._retriever = None  # 懒重建
        return True

    def _ensure_retriever(self):
        if self._retriever is None and self.chunks:
            documents = [c.text for c in self.chunks]
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer

                self._vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 3))
                self._matrix = self._vectorizer.fit_transform(documents)
                self._retriever = "tfidf_char_ngram"
            except Exception:
                from site_safety.agents.text_similarity import PortableCharTfidf

                self._portable_vectorizer = PortableCharTfidf(documents)
                self._retriever = "portable_tfidf_char_ngram"
        return self._retriever

    @_locked
    def prepare_index(self) -> str:
        """Eagerly build the local index so the first detection is not delayed."""
        self.refresh()
        return self._ensure_retriever() or "empty"

    @_locked
    def search(
        self, query: str, *, top_k: int = 5, min_score: float = 0.10
    ) -> List[dict]:
        self.refresh()
        if not query.strip() or self._ensure_retriever() is None:
            return []
        if self._retriever == "portable_tfidf_char_ngram":
            scores = self._portable_vectorizer.similarities(query)
        else:
            try:
                from sklearn.metrics.pairwise import cosine_similarity

                scores = cosine_similarity(
                    self._vectorizer.transform([query]), self._matrix
                )[0]
            except Exception:
                from site_safety.agents.text_similarity import PortableCharTfidf

                self._portable_vectorizer = PortableCharTfidf([c.text for c in self.chunks])
                self._retriever = "portable_tfidf_char_ngram"
                scores = self._portable_vectorizer.similarities(query)
        ranked = sorted(
            ((c, s) for c, s in zip(self.chunks, scores)
             if s >= min_score and c.metadata.get('effective_status') not in {'repealed', 'superseded'}),
            key=lambda x: x[1], reverse=True,
        )
        return [
            {
                "chunk_id": chunk.chunk_id,
                "source_file": chunk.source_file,
                "section": chunk.section,
                "text": chunk.text,
                "page_number": chunk.page_number,
                **chunk.metadata,
                "applicability": "requires_human_review",
                "score": round(float(score), 4),
            }
            for chunk, score in ranked[:top_k]
            if score >= min_score and chunk.metadata.get('effective_status') not in {'repealed', 'superseded'}
        ]

    @_locked
    def summary(self) -> dict:
        self.refresh()
        documents = []
        catalog = self._catalog()
        if self.kb_dir.is_dir():
            for path in sorted(self.kb_dir.iterdir()):
                if path.suffix.lower() not in {".md", ".txt", ".pdf", ".docx"}:
                    continue
                documents.append(
                    {
                        "source_file": path.name,
                        "size_bytes": path.stat().st_size,
                        "modified_at": path.stat().st_mtime,
                        "chunk_count": sum(c.source_file == path.name for c in self.chunks),
                        "excluded": bool(catalog.get(path.name, {}).get('excluded')),
                        "source_status": next((c.metadata.get('source_status') for c in self.chunks if c.source_file == path.name), 'not_indexed'),
                        "effective_status": next((c.metadata.get('effective_status') for c in self.chunks if c.source_file == path.name), 'unverified'),
                        "valid_until": next((c.metadata.get('valid_until', '') for c in self.chunks if c.source_file == path.name), ''),
                        "parse_warning": '；'.join(e['error'] for e in self.parse_errors if e['source_file'] == path.name),
                    }
                )
        return {
            "files": [item["source_file"] for item in documents],
            "documents": documents,
            "file_count": len(documents),
            "chunk_count": len(self.chunks),
            "retriever": self._retriever or "not_built",
            "parse_errors": list(self.parse_errors),
        }
