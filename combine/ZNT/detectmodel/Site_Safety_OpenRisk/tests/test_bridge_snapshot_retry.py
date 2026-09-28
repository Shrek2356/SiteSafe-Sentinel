import json
from pathlib import Path
from detect_bridge import DetectBridge


def test_temporary_windows_reader_lock_does_not_abort_job(tmp_path, monkeypatch):
    original = Path.replace
    calls = []
    def replace(path, target):
        calls.append(target)
        if len(calls) < 3:
            raise PermissionError('temporary Windows sharing violation')
        return original(path, target)
    monkeypatch.setattr(Path, 'replace', replace)
    monkeypatch.setattr('detect_bridge.time.sleep', lambda _: None)
    job = {'output_dir': str(tmp_path), 'status': 'done', 'job_id': 'JOB-test'}
    DetectBridge._persist_job(job)
    assert len(calls) == 3
    assert json.loads((tmp_path/'bridge_summary.json').read_text()) == job
