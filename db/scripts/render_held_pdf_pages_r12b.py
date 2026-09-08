#!/usr/bin/env python3
"""Read-only native-PDF rasterisation for R12B; no OCR or visual verdict.

JSON requests on stdin. Only hash-matching, already-held files are accepted.
PNG derivatives remain outside the repository, in the private render cache.
"""
import hashlib
from contextlib import redirect_stdout
import json
from io import BytesIO
from pathlib import Path
import re
import sys
import fitz

fitz.set_messages(stream=sys.stderr)


def run(requests):
    if fitz.VersionBind != '1.27.2.2':
        raise RuntimeError('RENDER_LIBRARY_VERSION_MISMATCH')
    root = Path('/private/tmp/coffee-flavor-r12b-render-cache')
    root.mkdir(parents=True, exist_ok=True)
    result = []
    for request in requests:
        fitz.TOOLS.mupdf_warnings(reset=True)
        body = Path(request['path']).read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != request['sha256']:
            raise ValueError('NOT_A_HASH_VERIFIED_HELD_DOCUMENT')
        native = body.startswith(b'%PDF')
        row = {'candidate_id': request['candidate_id'], 'source_sha256': digest,
               'renderer': 'PyMuPDF', 'renderer_version': fitz.VersionBind,
               'source_modality': 'ORIGINAL_HELD_PDF' if native else 'HELD_MARKUP_REFLOW_NOT_PUBLISHER_PAGES',
               'pages': [], 'anchors': [], 'all_table_anchor_ids': []}
        pdf_body = body
        if not native:
            # Rendering adapter only: independent of both table classifiers.
            # No table selection, row decoding, descriptor rules or grid reuse.
            markup = body.decode('utf-8', errors='replace')
            markup = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', '', markup, flags=re.I|re.S)
            markup = re.sub(r'<(?:link|meta)\b[^>]*>', '', markup, flags=re.I)
            row['unattached_graphic_count'] = len(re.findall(r'<(?:img|(?:\w+:)?graphic)\b', markup, flags=re.I))
            markup = re.sub(r'<(?:img|(?:\w+:)?graphic)\b[^>]*>', '[GRAPHIC NOT ATTACHED IN REFLOW]', markup, flags=re.I)
            markup = re.sub(r'<(/?)(?:\w+:)([\w-]+)', r'<\1\2', markup)
            markup = re.sub(r'<(/?)(?:sec|table-wrap|abstract|article)\b', r'<\1div', markup)
            markup = re.sub(r'<(/?)(?:article-title|title)\b', r'<\1h2', markup)
            def table_anchor(match):
                tag = match[0]
                existing = re.search(r'\bid=["\']([^"\']+)', tag)
                identifier = existing[1] if existing else 'r12b-source-table-' + str(len(row['all_table_anchor_ids']))
                row['all_table_anchor_ids'].append(identifier)
                return tag if existing else tag[:-1] + ' id="' + identifier + '">'
            markup = re.sub(r'<table\b[^>]*>', table_anchor, markup, flags=re.I)
            output_pdf = BytesIO()
            writer = fitz.DocumentWriter(output_pdf)
            def rectangle(index, filled):
                if index >= 300:
                    raise ValueError('REFLOW_PAGE_LIMIT_NOT_COMPLETE')
                page = fitz.Rect(0, 0, 842, 595)
                return page, fitz.Rect(30, 30, 812, 565), None
            try:
                def position(pos):
                    if pos.id:
                        row['anchors'].append({'id': pos.id, 'page': pos.page_num,
                            'open_close': pos.open_close, 'rect': list(pos.rect)})
                fitz.Story(html=markup).write(writer, rectangle, positionfn=position)
                writer.close()
                pdf_body = output_pdf.getvalue()
            except Exception as error:
                row.update(status='REFLOW_FAILED:' + type(error).__name__, detail=str(error)[:200])
                row['renderer_warnings'] = fitz.TOOLS.mupdf_warnings(reset=True)
                result.append(row)
                continue
        with fitz.open(stream=pdf_body, filetype='pdf') as document:
            pdf_path = root / f'{digest}-{"native" if native else "reflow"}.pdf'
            if native:
                pdf_path.write_bytes(body)
            else:
                document.xref_set_key(-1, 'ID', f'[<{digest[:32]}><{digest[:32]}>]')
                pdf_path.write_bytes(document.tobytes(no_new_id=True, garbage=4, deflate=True))
            row['pdf_path'] = str(pdf_path)
            row['pdf_sha256'] = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
            for index, page in enumerate(document):
                modality = 'native' if native else 'reflow'
                output = root / f'{digest}-{modality}-page-{index+1}.png'
                pixmap = page.get_pixmap(dpi=120, alpha=False)
                pixmap.save(str(output))
                row['pages'].append({'page_number': index+1, 'image_path': str(output),
                    'image_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                    'width': pixmap.width, 'height': pixmap.height,
                    'text_sha256': hashlib.sha256(page.get_text().encode()).hexdigest(),
                    'negative_section_marker_strict_v1': bool(re.search(r'(?im)^\s*(?:references|bibliography|materials and methods)\s*$', page.get_text())),
                    'negative_section_marker': bool(re.search(r'(?im)^\s*(?:\d+(?:\.\d+)*\.?\s+)?(?:references|bibliography|methods|materials and methods)\s*$', page.get_text())),
                    'vision_result': None})
        row['status'] = 'RENDERED_NOT_VISUALLY_ADJUDICATED'
        row['renderer_warnings'] = fitz.TOOLS.mupdf_warnings(reset=True)
        result.append(row)
    return result


if __name__ == '__main__':
    with redirect_stdout(sys.stderr):
        result = run(json.load(sys.stdin))
    print(json.dumps(result))
