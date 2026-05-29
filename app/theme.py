import os

from nicegui import ui

_STYLES_PATH = os.path.join(os.path.dirname(__file__), "static", "styles.css")

_LINE_NUMBER_JS = """
<script>
(function() {
  function process(code) {
    if (!code || code.dataset.lineNumbered === '1') return;
    code.dataset.lineNumbered = '1';
    var html = code.innerHTML;
    var lines = html.split('\\n');
    if (lines.length && lines[lines.length - 1] === '') lines.pop();
    code.innerHTML = lines.map(function(line, i) {
      return '<div class="code-line"><span class="code-ln">' + (i + 1) +
             '</span><span class="code-content">' + (line || ' ') + '</span></div>';
    }).join('');
  }
  function processAll(root) {
    (root || document).querySelectorAll('.card-body pre code').forEach(process);
  }
  window.applyLineNumbersAll = processAll;
})();
</script>
"""

_DOCK_JS = """
<script>
(function() {
  function autoResize(ta) {
    ta.style.height = 'auto';
    var h = Math.min(260, Math.max(96, ta.scrollHeight));
    ta.style.height = h + 'px';
  }
  document.addEventListener('input', function(e) {
    var t = e.target;
    if (t && t.matches && t.matches('.dock-input textarea')) autoResize(t);
  }, true);
  document.addEventListener('keydown', function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      var t = e.target;
      if (t && t.matches && t.matches('.dock-input textarea')) {
        e.preventDefault();
        var btn = document.querySelector('.dock .cmdbtn.primary');
        if (btn && !btn.disabled) btn.click();
      }
    }
  }, true);
  // resize once when the textarea first appears
  var obs = new MutationObserver(function(muts) {
    muts.forEach(function(m) {
      m.addedNodes.forEach(function(n) {
        if (n.nodeType !== 1) return;
        var tas = (n.matches && n.matches('.dock-input textarea'))
                  ? [n]
                  : (n.querySelectorAll ? n.querySelectorAll('.dock-input textarea') : []);
        tas.forEach(autoResize);
      });
    });
  });
  if (document.readyState !== 'loading') obs.observe(document.body, { childList: true, subtree: true });
  else document.addEventListener('DOMContentLoaded', function() { obs.observe(document.body, { childList: true, subtree: true }); });
})();
</script>
"""


def apply_theme():
    try:
        styles_version = int(os.path.getmtime(_STYLES_PATH))
    except OSError:
        styles_version = 0
    ui.add_head_html(f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/styles.css?v={styles_version}">
    """ + _LINE_NUMBER_JS + _DOCK_JS)
