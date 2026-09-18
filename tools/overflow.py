# -*- coding: utf-8 -*-
"""가로 오버플로를 일으키는 요소를 찾는다. 모바일 폭에서 화면이 밀리는 원인."""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
URL = sys.argv[2] if len(sys.argv) > 2 else None

inj = (
    "<script>window.addEventListener('load',function(){setTimeout(function(){"
    "var vw=document.documentElement.clientWidth,bad=[];"
    "document.querySelectorAll('*').forEach(function(e){var r=e.getBoundingClientRect();"
    "if(r.width>0&&(r.right>vw+1.5||r.left<-1.5)){"
    "var s=e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'"
    "?'.'+e.className.trim().split(/\\s+/).slice(0,2).join('.'):'');"
    "bad.push(s+' ['+Math.round(r.left)+'..'+Math.round(r.right)+']');}});"
    "document.title='@@vw='+vw+' docW='+document.documentElement.scrollWidth"
    "+' | '+bad.slice(0,14).join(' | ')+'@@';},800);});</script>"
)

if URL:
    target = URL
else:
    src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    tmp = os.path.join(ROOT, "_ov.html")
    io.open(tmp, "w", encoding="utf-8").write(src.replace("</body>", inj + "</body>"))
    target = "file:///" + tmp.replace("\\", "/")

p = subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--force-device-scale-factor=1",
                    "--window-size=%d,844" % W, "--virtual-time-budget=10000", "--dump-dom", target],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
if not URL:
    os.remove(os.path.join(ROOT, "_ov.html"))
m = re.search(r"@@(.*?)@@", p.stdout or "", re.S)
if not m:
    print("리포트 없음"); sys.exit(1)
for part in m.group(1).split(" | "):
    print(part)
