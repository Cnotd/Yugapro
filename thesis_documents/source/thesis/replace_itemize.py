#!/usr/bin/env python3
"""将 thesis_yoga.tex 中的 itemize 替换为 researchlist"""
import re

input_file = 'd:/yuga_test/thesis/thesis_yoga.tex'
output_file = 'd:/yuga_test/thesis/thesis_yoga.tex'

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 统计
itemize_count = len(re.findall(r'\\begin\{itemize\}', content))
item_count = len(re.findall(r'\\item', content))

print(f"找到 {itemize_count} 个 itemize 环境")
print(f"找到 {item_count} 个 \\item")

# 替换 itemize -> researchlist
content = content.replace(r'\begin{itemize}', r'\begin{researchlist}')
content = content.replace(r'\end{itemize}', r'\end{researchlist}')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n已替换完成！")
print(f"- {itemize_count} 个 \\begin{{itemize}} -> \\begin{{researchlist}}")
print(f"- {itemize_count} 个 \\end{{itemize}} -> \\end{{researchlist}}")
