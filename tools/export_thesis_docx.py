import re
import zipfile
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("w", W_NS)


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def collapse_whitespace(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_comments(text: str) -> str:
    cleaned_lines = []
    for line in text.splitlines():
        out = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "%" and (i == 0 or line[i - 1] != "\\"):
                break
            out.append(ch)
            i += 1
        cleaned_lines.append("".join(out))
    return "\n".join(cleaned_lines)


def extract_braced(text: str, start: int):
    assert text[start] == "{"
    depth = 0
    i = start
    buf = []
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
            if depth > 1:
                buf.append(ch)
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return "".join(buf), i + 1
            buf.append(ch)
        else:
            buf.append(ch)
        i += 1
    return "".join(buf), i


def replace_command_arg(text: str, command: str, replacer):
    pattern = f"\\{command}" + "{"
    i = 0
    parts = []
    while i < len(text):
        idx = text.find(pattern, i)
        if idx == -1:
            parts.append(text[i:])
            break
        parts.append(text[i:idx])
        content, end = extract_braced(text, idx + len(command) + 1)
        parts.append(replacer(content))
        i = end
    return "".join(parts)


def latex_to_plain(text: str) -> str:
    text = text.replace("~", "")
    text = text.replace("\\\\", "\n")
    text = text.replace("\\quad", " ")
    text = text.replace("\\qquad", " ")
    text = text.replace("\\,", " ")
    text = text.replace("\\%", "%")
    text = text.replace("\\_", "_")
    text = text.replace("\\{", "{")
    text = text.replace("\\}", "}")
    text = text.replace("\\$", "$")
    text = re.sub(r"\$([^$]+)\$", r"\1", text)

    for cmd in [
        "textbf",
        "texttt",
        "textit",
        "textrm",
        "emph",
        "TNR",
        "coverline",
        "underline",
        "songti",
        "heiti",
        "kaishu",
        "rmfamily",
        "path",
        "url",
    ]:
        text = replace_command_arg(text, cmd, lambda x: latex_to_plain(x))

    for cmd in [
        "zihao",
        "setstretch",
        "thispagestyle",
        "addcontentsline",
        "pagenumbering",
    ]:
        text = replace_command_arg(text, cmd, lambda x: "")

    # Special cases with multiple args.
    text = re.sub(r"\\makebox(?:\[[^\]]*\]){1,2}\{", "{", text)
    text = re.sub(r"\\coverline\{[^{}]*\}\{", r"{", text)
    text = replace_command_arg(text, "chapter", lambda x: latex_to_plain(x))
    text = replace_command_arg(text, "chapter*", lambda x: latex_to_plain(x))
    text = replace_command_arg(text, "section", lambda x: latex_to_plain(x))
    text = replace_command_arg(text, "subsection", lambda x: latex_to_plain(x))
    text = replace_command_arg(text, "subsubsection", lambda x: latex_to_plain(x))
    text = replace_command_arg(text, "caption", lambda x: latex_to_plain(x))
    text = replace_command_arg(text, "label", lambda x: "")
    text = replace_command_arg(text, "ref", lambda x: "")
    text = replace_command_arg(text, "addcontentsline", lambda x: "")

    text = re.sub(r"\\hspace\*?\{[^{}]*\}", " ", text)
    text = re.sub(r"\\vspace\*?\{[^{}]*\}", "\n", text)
    text = re.sub(r"\\includegraphics(\[[^\]]*\])?\{[^{}]*\}", "", text)
    text = re.sub(r"\\[A-Za-z@]+(\[[^\]]*\])?", "", text)
    text = re.sub(r"\[(?:-?\d+(?:\.\d+)?(?:em|cm|pt|ex)?|[slcr])\]", "", text)
    text = text.replace("{", "").replace("}", "")
    text = collapse_whitespace(text)
    return text


def parse_tex(tex: str):
    body_match = re.search(r"\\begin\{document\}(.*)\\end\{document\}", tex, re.S)
    if not body_match:
        raise ValueError("Could not find document body")
    body = body_match.group(1)
    body = strip_comments(body)

    paragraphs = []
    lines = body.splitlines()
    i = 0
    chapter_num = 0
    section_num = 0
    subsection_num = 0
    enum_stack = []
    in_verbatim = False
    in_equation = False
    in_figure = False
    in_longtable = False
    in_tabular = False
    code_lines = []
    eq_lines = []
    figure_caption = None
    table_lines = []

    def add_paragraph(text, style="Normal"):
        text = collapse_whitespace(text)
        if text:
            paragraphs.append((style, text))

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if in_verbatim:
                code_lines.append("")
            elif in_equation:
                eq_lines.append("")
            elif in_longtable or in_tabular:
                table_lines.append("")
            continue

        if line.startswith(r"\begin{verbatim}"):
            in_verbatim = True
            code_lines = []
            continue
        if line.startswith(r"\end{verbatim}"):
            in_verbatim = False
            add_paragraph("\n".join(code_lines), "Code")
            code_lines = []
            continue
        if in_verbatim:
            code_lines.append(raw_line.rstrip())
            continue

        if line.startswith(r"\begin{equation}"):
            in_equation = True
            eq_lines = []
            continue
        if line.startswith(r"\end{equation}"):
            in_equation = False
            add_paragraph("公式：" + " ".join(eq_lines), "Quote")
            eq_lines = []
            continue
        if in_equation:
            eq_lines.append(line)
            continue

        if line.startswith(r"\begin{figure}"):
            in_figure = True
            figure_caption = None
            continue
        if in_figure and r"\caption{" in line:
            m = re.search(r"\\caption\{(.+)\}", line)
            if m:
                figure_caption = latex_to_plain(m.group(1))
            continue
        if line.startswith(r"\end{figure}"):
            if figure_caption:
                add_paragraph("图： " + figure_caption, "Caption")
            else:
                add_paragraph("图：", "Caption")
            in_figure = False
            figure_caption = None
            continue
        if in_figure:
            continue

        if line.startswith(r"\begin{longtable}") or line.startswith(r"\begin{tabular}"):
            in_longtable = line.startswith(r"\begin{longtable}")
            in_tabular = line.startswith(r"\begin{tabular}")
            table_lines = []
            continue
        if line.startswith(r"\end{longtable}") or line.startswith(r"\end{tabular}"):
            for row in table_lines:
                row = row.strip()
                if not row or row.startswith(r"\toprule") or row.startswith(r"\midrule") or row.startswith(r"\bottomrule"):
                    continue
                row = row.replace(r"\\", "")
                row = row.replace("&", "    ")
                row = latex_to_plain(row)
                if row:
                    add_paragraph(row, "Quote")
            in_longtable = False
            in_tabular = False
            table_lines = []
            continue
        if in_longtable or in_tabular:
            if not line.startswith(r"\caption") and not line.startswith(r"\label") and not line.startswith(r"\endfirsthead") and not line.startswith(r"\endhead"):
                table_lines.append(line)
            continue

        if line.startswith(r"\begin{titlepage}") or line.startswith(r"\end{titlepage}"):
            continue
        if line.startswith(r"\clearpage") or line.startswith(r"\newpage") or line.startswith(r"\makeatletter") or line.startswith(r"\makeatother"):
            continue
        if line.startswith(r"\pagenumbering") or line.startswith(r"\pagestyle") or line.startswith(r"\fancy") or line.startswith(r"\setlength"):
            continue

        m = re.match(r"\\heitchapter\{(.+)\}", line)
        if m:
            add_paragraph(latex_to_plain(m.group(1)), "Heading1")
            continue

        m = re.match(r"\\chapter\*?\{(.+)\}", line)
        if m:
            title = latex_to_plain(m.group(1))
            chapter_num += 1
            section_num = 0
            subsection_num = 0
            add_paragraph(title, "Heading1")
            continue

        m = re.match(r"\\section\{(.+)\}", line)
        if m:
            title = latex_to_plain(m.group(1))
            section_num += 1
            subsection_num = 0
            add_paragraph(title, "Heading2")
            continue

        m = re.match(r"\\subsection\{(.+)\}", line)
        if m:
            title = latex_to_plain(m.group(1))
            subsection_num += 1
            add_paragraph(title, "Heading3")
            continue

        m = re.match(r"\\subsubsection\{(.+)\}", line)
        if m:
            title = latex_to_plain(m.group(1))
            add_paragraph(title, "Heading4")
            continue

        if line.startswith(r"\begin{chineseenum}") or line.startswith(r"\begin{enumerate}"):
            enum_stack.append(0)
            continue
        if line.startswith(r"\end{chineseenum}") or line.startswith(r"\end{enumerate}"):
            if enum_stack:
                enum_stack.pop()
            continue
        if line.startswith(r"\item"):
            if enum_stack:
                enum_stack[-1] += 1
                prefix = f"{enum_stack[-1]}. "
            else:
                prefix = "• "
            add_paragraph(prefix + latex_to_plain(line[len(r"\item"):].strip()))
            continue

        if line.startswith(r"\begin{center}") or line.startswith(r"\end{center}"):
            continue

        if line.startswith(r"\begin{"):
            continue
        if line.startswith(r"\end{"):
            continue

        plain = latex_to_plain(line)
        if plain:
            add_paragraph(plain)

    # Merge broken adjacent short normal paragraphs from wrapped source lines.
    merged = []
    for style, text in paragraphs:
        if merged and style == "Normal" and merged[-1][0] == "Normal":
            prev = merged[-1][1]
            if len(prev) > 20 and not prev.endswith(("。", "；", "：", "？", "！", "”")):
                merged[-1] = ("Normal", prev + text)
                continue
        merged.append((style, text))
    return merged


def make_paragraph(text: str, style: str = "Normal"):
    p = ET.Element(w_tag("p"))
    pPr = ET.SubElement(p, w_tag("pPr"))
    if style and style != "Normal":
        pStyle = ET.SubElement(pPr, w_tag("pStyle"))
        pStyle.set(w_tag("val"), style)
    if style == "Caption":
        jc = ET.SubElement(pPr, w_tag("jc"))
        jc.set(w_tag("val"), "center")

    for idx, part in enumerate(text.split("\n")):
        if idx:
            r_br = ET.SubElement(p, w_tag("r"))
            ET.SubElement(r_br, w_tag("br"))
        r = ET.SubElement(p, w_tag("r"))
        t = ET.SubElement(r, w_tag("t"))
        if part.startswith(" ") or part.endswith(" "):
            t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = part
    return p


def replace_document_body(template_docx: Path, output_docx: Path, paragraphs):
    with zipfile.ZipFile(template_docx, "r") as zin:
        files = {name: zin.read(name) for name in zin.namelist()}

    root = ET.fromstring(files["word/document.xml"])
    body = root.find(w_tag("body"))
    if body is None:
        raise ValueError("Could not find Word body")

    sectPr = None
    if len(body) and body[-1].tag == w_tag("sectPr"):
        sectPr = deepcopy(body[-1])

    for child in list(body):
        body.remove(child)

    for style, text in paragraphs:
        body.append(make_paragraph(text, style))

    if sectPr is not None:
        body.append(sectPr)

    files["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)


def main():
    root = Path(__file__).resolve().parent
    tex_path = root / "thesis_yoga.tex"
    template_docx = root / "temp_outline.docx"
    output_docx = root / "thesis_yoga.docx"

    tex = tex_path.read_text(encoding="utf-8")
    paragraphs = parse_tex(tex)
    replace_document_body(template_docx, output_docx, paragraphs)
    print(f"Created: {output_docx}")
    print(f"Paragraphs: {len(paragraphs)}")


if __name__ == "__main__":
    main()
