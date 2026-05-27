"""
Convierte un markdown a PDF preservando ecuaciones LaTeX vía MathJax.

Uso:
    python scripts/md_to_pdf.py <input.md> [<output.pdf>]

Si se omite output, se genera junto al .md con la misma raíz y extension .pdf.

Requiere:
    - Python con paquete `markdown` instalado.
    - Microsoft Edge (modo headless para imprimir HTML a PDF).
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown


EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true
  }},
  options: {{
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
  }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>
  body {{
    font-family: Georgia, "Times New Roman", serif;
    max-width: 820px;
    margin: 2em auto;
    padding: 0 1.5em;
    line-height: 1.55;
    color: #222;
    font-size: 11pt;
  }}
  h1, h2, h3, h4, h5 {{
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: #111;
    font-weight: 600;
    line-height: 1.25;
  }}
  h1 {{
    font-size: 1.9em;
    border-bottom: 2px solid #bbb;
    padding-bottom: 0.3em;
    margin-top: 0;
  }}
  h2 {{
    font-size: 1.45em;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.2em;
    margin-top: 2em;
  }}
  h3 {{ font-size: 1.2em; margin-top: 1.5em; }}
  h4 {{ font-size: 1.05em; margin-top: 1.2em; }}
  p {{ margin: 0.7em 0; }}
  ul, ol {{ margin: 0.5em 0 0.8em 1.5em; padding: 0; }}
  li {{ margin: 0.25em 0; }}
  code {{
    background: #f4f4f4;
    padding: 0.1em 0.35em;
    border-radius: 3px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 0.93em;
  }}
  pre {{
    background: #f4f4f4;
    padding: 0.9em 1em;
    border-radius: 5px;
    overflow-x: auto;
    border: 1px solid #e5e5e5;
  }}
  pre code {{ background: none; padding: 0; }}
  table {{
    border-collapse: collapse;
    margin: 1em 0;
    width: 100%;
    font-size: 0.95em;
  }}
  th, td {{
    padding: 0.4em 0.7em;
    border: 1px solid #d8d8d8;
    text-align: left;
    vertical-align: top;
  }}
  th {{ background: #eef0f2; font-weight: 600; }}
  blockquote {{
    border-left: 4px solid #b8c4d0;
    margin: 1em 0;
    padding: 0.4em 1em;
    color: #444;
    background: #f7f9fb;
    font-style: italic;
  }}
  hr {{
    border: none;
    border-top: 1px solid #ccc;
    margin: 2em 0;
  }}
  a {{ color: #2c5aa0; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  mjx-container {{ font-size: 1em !important; }}
  @media print {{
    body {{
      max-width: none;
      margin: 0;
      padding: 1cm 1.5cm;
      font-size: 10.5pt;
    }}
    h2 {{ page-break-before: auto; }}
    h2, h3 {{ page-break-after: avoid; }}
    table, pre, blockquote {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def md_to_html(md_text: str) -> str:
    """Convierte markdown a HTML preservando bloques LaTeX intactos."""
    # Stash math blocks para que markdown.py no los toque (puede malinterpretar
    # _, *, etc. dentro de fórmulas).
    math_blocks: list[str] = []

    def stash(m: re.Match) -> str:
        idx = len(math_blocks)
        math_blocks.append(m.group(0))
        return f"@@MATH{idx}@@"

    # Display math primero (greedy lazy)
    md_text = re.sub(r"\$\$[\s\S]+?\$\$", stash, md_text)
    # Inline math: requiere que no haya newlines, evita falsos positivos
    md_text = re.sub(r"\$[^\$\n]+?\$", stash, md_text)

    html = markdown.markdown(
        md_text,
        extensions=["extra", "tables", "sane_lists", "smarty"],
        output_format="html5",
    )

    # Restaurar math
    def restore(m: re.Match) -> str:
        idx = int(m.group(1))
        return math_blocks[idx]

    html = re.sub(r"@@MATH(\d+)@@", restore, html)
    return html


def render_pdf(md_path: Path, pdf_path: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    body_html = md_to_html(md_text)

    title = md_path.stem.replace("_", " ").replace("-", " ").title()
    full_html = HTML_TEMPLATE.format(title=title, body=body_html)

    # Escribir HTML temporal en el mismo directorio para que rutas relativas
    # funcionen (no que vamos a usar imágenes, pero por las dudas).
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".html",
        delete=False,
        dir=str(md_path.parent),
    ) as tmp:
        tmp.write(full_html)
        tmp_html_path = Path(tmp.name)

    try:
        edge = Path(EDGE_PATH)
        if not edge.exists():
            raise FileNotFoundError(f"Edge no encontrado en {EDGE_PATH}")

        # virtual-time-budget da tiempo a MathJax para renderizar todas las
        # ecuaciones antes de que se capture el PDF.
        cmd = [
            str(edge),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--virtual-time-budget=15000",
            f"--print-to-pdf={pdf_path}",
            tmp_html_path.as_uri(),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print("STDOUT:", result.stdout, file=sys.stderr)
            print("STDERR:", result.stderr, file=sys.stderr)
            raise RuntimeError(f"Edge fallo con codigo {result.returncode}")
    finally:
        try:
            tmp_html_path.unlink()
        except OSError:
            pass


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    md_path = Path(sys.argv[1]).resolve()
    if not md_path.exists():
        print(f"No existe: {md_path}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) >= 3:
        pdf_path = Path(sys.argv[2]).resolve()
    else:
        pdf_path = md_path.with_suffix(".pdf")

    render_pdf(md_path, pdf_path)
    print(f"PDF generado: {pdf_path}")


if __name__ == "__main__":
    main()
