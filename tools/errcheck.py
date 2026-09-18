# -*- coding: utf-8 -*-
"""페이지를 띄워 JS 오류와 깨진 리소스를 모은다."""
import io
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"

head = ("<script>window.__e=[];window.addEventListener('error',function(ev){"
        "var t=ev.target;if(t&&t.tagName==='IMG')window.__e.push('IMG '+t.getAttribute('src'));"
        "else window.__e.push('JS '+(ev.message||'')+' @'+(ev.filename||'')+':'+(ev.lineno||''));"
        "},true);window.addEventListener('unhandledrejection',function(e){"
        "window.__e.push('PROMISE '+e.reason);});</script>")

tail = ("<script>window.addEventListener('load',function(){setTimeout(function(){"
        "var bad=[];document.querySelectorAll('img').forEach(function(im){"
        "if(im.getAttribute('loading')!=='lazy'&&im.complete&&im.naturalWidth===0)"
        "bad.push(im.getAttribute('src'));});"
        "document.title='@@'+JSON.stringify({err:window.__e.slice(0,12),img:bad.slice(0,12)})+'@@';"
        "},900);});</script>")

src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
tmp = os.path.join(ROOT, "_err.html")
io.open(tmp, "w", encoding="utf-8").write(
    src.replace("<head>", "<head>" + head).replace("</body>", tail + "</body>"))

p = subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--window-size=1440,900",
                    "--virtual-time-budget=14000", "--dump-dom",
                    "file:///" + tmp.replace("\\", "/")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
os.remove(tmp)
m = re.search(r"@@(.*?)@@", p.stdout or "", re.S)
print(m.group(1) if m else "리포트 없음")
