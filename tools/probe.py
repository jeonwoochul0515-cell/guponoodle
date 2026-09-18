# -*- coding: utf-8 -*-
"""스크롤 위치에서 각 샷이 실제로 어떤 상태인지 덤프한다."""
import io
import os
import re
import subprocess
import sys

POLY = ("<script>window.requestAnimationFrame=function(cb){"
        "return setTimeout(function(){cb(Date.now());},16);};</script>")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.20

inj = (
    "<script>(function(){document.documentElement.style.scrollBehavior='auto';"
    "function go(){var sec=document.getElementById('cine');"
    "var top=sec.offsetTop,len=sec.offsetHeight-window.innerHeight;"
    "window.scrollTo({top:Math.round(top+len*" + repr(R) + "),behavior:'instant'});"
    "window.dispatchEvent(new Event('scroll'));}"
    "window.addEventListener('load',function(){var n=0,id=setInterval(function(){go();"
    "if(++n>120){clearInterval(id);report();}},16);});"
    "function report(){var sec=document.getElementById('cine');"
    "var r=sec.getBoundingClientRect();var out=['SY='+Math.round(window.scrollY),"
    "'secH='+sec.offsetHeight,'top='+Math.round(r.top),"
    "'dolly='+(document.getElementById('cine-dolly').style.transform||'-')];"
    "document.querySelectorAll('.shot').forEach(function(s,i){var im=s.querySelector('img');"
    "out.push(i+':vis='+(s.style.visibility||'-')+',op='+(s.style.opacity||'-')"
    "+',ok='+(im.complete&&im.naturalWidth>0)+',tf='+((s.style.transform||'-').slice(0,46)));});"
    "document.title='@@'+out.join('|')+'@@';}})();</script>"
)

src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
tmp = os.path.join(ROOT, "_probe.html")
io.open(tmp, "w", encoding="utf-8").write(src.replace("<head>", "<head>"+POLY).replace("</body>", inj + "</body>"))

p = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--window-size=1440,810", "--virtual-time-budget=15000", "--dump-dom",
                    "file:///" + tmp.replace("\\", "/")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
os.remove(tmp)
m = re.search(r"@@(.*?)@@", p.stdout or "", re.S)
if not m:
    print("리포트를 찾지 못했다"); sys.exit(1)
for line in m.group(1).split("|"):
    print(line)
