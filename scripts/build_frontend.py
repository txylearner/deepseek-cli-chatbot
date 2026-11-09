"""把 frontend/ 下的源码内联并压缩成一个 index.html。

为什么需要构建：
    浏览器只能拿到 HTML / CSS / JS，源码必须下发。为了让随手查看
    变得困难，这里把三个文件合成一个页面，并压缩掉注释和空白。
    真正的业务逻辑（提示词、模型调用、数据库）始终在服务端。

用法：
    python scripts/build_frontend.py          # 生成 src/chatbot/static/index.html
    python scripts/build_frontend.py --check  # 只检查产物是否最新（CI 用）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import rjsmin
except ImportError:  # pragma: no cover - 构建环境提示
    raise SystemExit("缺少构建依赖，请先执行：python -m pip install rjsmin")

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
OUTPUT = ROOT / "src" / "chatbot" / "static" / "index.html"

STYLE_TAG = '<link rel="stylesheet" href="css/app.css" />'
SCRIPT_TAG = '<script src="js/app.js" defer></script>'


def minify_css(css: str) -> str:
    """保守压缩：去注释、合并空白、去掉括号和分号两侧的空格。"""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};])\s*", r"\1", css)
    css = css.replace(";}", "}")
    return css.strip()


def minify_html(html: str) -> str:
    """只做安全处理：去行尾空白、去空行、压缩标签之间的空白。"""
    lines = [line.rstrip() for line in html.splitlines()]
    html = "\n".join(line for line in lines if line)
    html = re.sub(r">\s+<", "><", html)
    return html.strip() + "\n"


def render() -> str:
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    css = minify_css((FRONTEND / "css" / "app.css").read_text(encoding="utf-8"))
    javascript = rjsmin.jsmin((FRONTEND / "js" / "app.js").read_text(encoding="utf-8"))

    if STYLE_TAG not in html or SCRIPT_TAG not in html:
        raise SystemExit("frontend/index.html 里找不到样式或脚本占位标签")

    html = html.replace(STYLE_TAG, f"<style>{css}</style>")
    html = html.replace(SCRIPT_TAG, f"<script>{javascript}</script>")
    return minify_html(html)


def main() -> int:
    built = render()

    if "--check" in sys.argv:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != built:
            print("构建产物不是最新，请运行：python scripts/build_frontend.py")
            return 1
        print("构建产物已是最新")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(built, encoding="utf-8")
    print(f"已生成 {OUTPUT.relative_to(ROOT)}（{len(built)} 字符）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
