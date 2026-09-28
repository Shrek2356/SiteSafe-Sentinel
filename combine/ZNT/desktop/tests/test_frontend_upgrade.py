"""Upgrades refresh the HTML entry without erasing saved user settings."""
import http.client
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_app import SpaHandler, ReusableThreadingHTTPServer, frontend_entry_url


def test_entry_address_changes_with_frontend_content(tmp_path):
    entry = tmp_path / 'index.html'
    entry.write_text('<html>old</html>')
    old = frontend_entry_url(5173, tmp_path)
    assert old == frontend_entry_url(5173, tmp_path)
    entry.write_text('<html>new</html>')
    assert old != frontend_entry_url(5173, tmp_path)
    assert old.startswith('http://127.0.0.1:5173/login?build=')


@pytest.mark.parametrize('route', ['/', '/index.html', '/login?build=new', '/dashboard'])
def test_html_never_returns_cached_304(tmp_path, route):
    (tmp_path / 'index.html').write_text('<html>new build</html>')
    server = ReusableThreadingHTTPServer(('127.0.0.1', 0),
        lambda *args, **kw: SpaHandler(*args, directory=str(tmp_path), **kw))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    try:
        client.request('GET', route, headers={'If-Modified-Since': 'Wed, 01 Jan 2098 00:00:00 GMT'})
        response = client.getresponse()
        assert response.status == 200
        assert 'no-store' in response.getheader('Cache-Control')
        assert response.read() == b'<html>new build</html>'
    finally:
        client.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
