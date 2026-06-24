"""
简历 PDF 生成脚本
用法：
    python resume_to_pdf.py                    # 默认：读取同目录 index.html，输出 resume.pdf
    python resume_to_pdf.py --html my.html     # 指定输入 HTML
    python resume_to_pdf.py --pdf out.pdf      # 指定输出 PDF
    python resume_to_pdf.py --dir D:/resume    # 指定工作目录，自动查找 index.html 并输出 resume.pdf
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("错误：未安装 playwright。请先运行：pip install playwright && playwright install chromium")
    sys.exit(1)


def generate_pdf(html_path: str, pdf_path: str) -> None:
    html_path = os.path.abspath(html_path)
    pdf_path = os.path.abspath(pdf_path)

    if not os.path.isfile(html_path):
        raise FileNotFoundError(f"找不到 HTML 文件：{html_path}")

    file_url = Path(html_path).as_uri()

    print(f"输入：{html_path}")
    print(f"输出：{pdf_path}")
    print("正在生成 PDF ...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(file_url)
        page.wait_for_load_state("networkidle")
        page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()

    print(f"完成！PDF 已保存到：{pdf_path}")


def main():
    parser = argparse.ArgumentParser(description="将简历 HTML 转换为 A4 PDF")
    parser.add_argument("--html", help="输入 HTML 文件路径", default=None)
    parser.add_argument("--pdf", help="输出 PDF 文件路径", default=None)
    parser.add_argument("--dir", help="工作目录（默认：脚本所在目录）", default=None)

    args = parser.parse_args()

    base_dir = os.path.abspath(args.dir) if args.dir else os.path.dirname(os.path.abspath(__file__))

    html_path = args.html or os.path.join(base_dir, "index.html")
    pdf_path = args.pdf or os.path.join(base_dir, "resume.pdf")

    try:
        generate_pdf(html_path, pdf_path)
    except Exception as e:
        print(f"失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
