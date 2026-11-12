#!/usr/bin/env python3
"""빌드 전 검사: 스크립트가 찾는 화면 요소(id)가 HTML에 모두 있는지 확인한다."""
import re, sys, pathlib
src = pathlib.Path(__file__).with_name('index.html').read_text(encoding='utf-8')
used = set(re.findall(r"\$\('([A-Za-z0-9_-]+)'\)", src)) | set(re.findall(r"getElementById\('([A-Za-z0-9_-]+)'\)", src))
have = set(re.findall(r'\bid="([A-Za-z0-9_-]+)"', src))
missing = sorted(used - have)
if missing:
    print('빠진 화면 요소:', ', '.join(missing)); sys.exit(1)
print(f'화면 요소 검사 통과 ({len(used)}개)')
