"""
Wiki 文本差异对比工具
=====================
用法：python aidiff.py <原文文件> <新文文件>

对比两个 .wikitext 文件，生成 HTML 格式的差异报告，
并自动在浏览器中打开。

输出文件保存在本目录下，文件名为：
    diff_{原文文件名}_vs_{新文文件名}_{时间戳}.html
"""

import difflib
import os
import sys
import webbrowser
from datetime import datetime


def generate_diff_html(text1: str, text2: str, fromdesc: str = "原文", todesc: str = "修改版") -> str:
    """生成 HTML 差异对比报告，返回 HTML 内容。"""
    diff = difflib.HtmlDiff(wrapcolumn=80)

    lines1 = text1.splitlines()
    lines2 = text2.splitlines()

    html = diff.make_file(lines1, lines2, fromdesc=fromdesc, todesc=todesc)
    return html


def save_diff_html(html: str, name1: str, name2: str) -> str:
    """将 HTML 写入文件，返回文件路径。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base1 = os.path.splitext(os.path.basename(name1))[0]
    base2 = os.path.splitext(os.path.basename(name2))[0]
    out_name = f"diff_{base1}_vs_{base2}_{ts}.html"
    out_path = os.path.join(os.path.dirname(__file__), out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    return out_path


def open_in_browser(path: str) -> None:
    """在默认浏览器中打开 HTML 文件。"""
    abs_path = os.path.abspath(path)
    webbrowser.open_new_tab(f"file://{abs_path}")


def main() -> None:
    if len(sys.argv) != 3:
        print("用法：python aidiff.py <原文.txt> <新文.txt>")
        print("示例：python aidiff.py ../cache/示例页面_20260524_original.wikitext ../cache/示例页面_20260524_modified.wikitext")
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]

    if not os.path.isfile(file1):
        print(f"错误：找不到文件 {file1}")
        sys.exit(1)
    if not os.path.isfile(file2):
        print(f"错误：找不到文件 {file2}")
        sys.exit(1)

    with open(file1, "r", encoding="utf-8") as f:
        t1 = f.read()
    with open(file2, "r", encoding="utf-8") as f:
        t2 = f.read()

    fromdesc = os.path.basename(file1)
    todesc = os.path.basename(file2)
    html = generate_diff_html(t1, t2, fromdesc=fromdesc, todesc=todesc)
    out_path = save_diff_html(html, file1, file2)

    print(f"差异报告已生成：{out_path}")
    print("正在打开浏览器...")
    open_in_browser(out_path)


if __name__ == "__main__":
    main()
