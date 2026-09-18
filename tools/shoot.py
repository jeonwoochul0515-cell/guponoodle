# -*- coding: utf-8 -*-
"""index.html을 스크롤 위치별로 캡처해서 시네마 히어로가 실제로 도는지 눈으로 본다."""
import io
import os
import subprocess
import sys

POLY = ("<script>window.requestAnimationFrame=function(cb){"
        "return setTimeout(function(){cb(Date.now());},16);};</script>")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PREV = os.path.join(ROOT, ".preview")
os.makedirs(PREV, exist_ok=True)

ratios = [float(a) for a in sys.argv[1:]] or [0.0, 0.06, 0.16, 0.28, 0.40, 0.55, 0.70, 0.86, 0.97]
src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

for r in ratios:
    # 스크롤로 상태를 만든 뒤, 그 순간을 복제해 정적 페이지로 바꿔 찍는다.
    # headless는 sticky + preserve-3d 조합을 그대로 합성하지 못한다.
    inject = (
        "<script>(function(){var R=%f;"
        "document.documentElement.style.scrollBehavior='auto';"
        "function go(){var sec=document.getElementById('cine');"
        "var top=sec.offsetTop, len=sec.offsetHeight-window.innerHeight;"
        "window.scrollTo({top:Math.round(top+len*R),behavior:'instant'});"
        "window.dispatchEvent(new Event('scroll'));}"
        "function freeze(){var sec=document.getElementById('cine');"
        "var c=sec.cloneNode(true);"
        "c.querySelector('.cine-track').style.height='100vh';"
        "var st=c.querySelector('.cine-sticky');"
        "st.style.position='static';st.style.height='100vh';"
        "document.body.textContent='';document.body.style.margin='0';"
        "document.body.appendChild(c);window.scrollTo(0,0);}"
        "window.addEventListener('load',function(){var n=0,id=setInterval(function(){"
        "go();if(++n>140){clearInterval(id);freeze();}},16);});})();</script>" % r
    )
    tmp = os.path.join(ROOT, "_shot_tmp.html")
    io.open(tmp, "w", encoding="utf-8").write(src.replace("<head>", "<head>"+POLY).replace("</body>", inject + "</body>"))
    out = os.path.join(PREV, "scroll-%03d.png" % int(r * 100))
    subprocess.run([
        CHROME, "--headless=new", "--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox", "--hide-scrollbars",
        "--force-device-scale-factor=1", "--window-size=1440,810",
        "--virtual-time-budget=20000",
        "--screenshot=" + out.replace("\\", "/"),
        "file:///" + os.path.join(ROOT, "_shot_tmp.html").replace("\\", "/"),
    ], capture_output=True)
    os.remove(tmp)
    print("%.2f -> %s (%d KB)" % (r, os.path.basename(out),
                                  os.path.getsize(out) // 1024 if os.path.exists(out) else -1))
