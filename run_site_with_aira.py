"""AIRA V2 companion launcher for unchanged main_12-11-2026.py.
Local development only. Start widget_server.py separately on port 8765.
"""
from pathlib import Path
import runpy
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / 'main_12-11-2026.py'
if not ORIGINAL.is_file():
    raise FileNotFoundError(
        'Sila SALIN main_12-11-2026.py ke folder ini (di sebelah run_site_with_aira.py). '
        'Fail website asal tidak diubah.'
    )

# Preserve original website behavior. The accompanying launcher does not edit it.
runpy.run_path(str(ORIGINAL), run_name='__main__')

# Local test bridge. Some Streamlit/browser versions may block iframe-to-parent injection.
components.html('''<script>
try {
  const doc = window.parent.document;
  if (!doc.getElementById('aira-bridge-loader')) {
    const script = doc.createElement('script');
    script.id = 'aira-bridge-loader';
    script.src = 'http://127.0.0.1:8765/embed.js';
    doc.body.appendChild(script);
  }
} catch (error) {
  console.error('AIRA widget injection blocked by iframe security', error);
}
</script>''', height=0)
