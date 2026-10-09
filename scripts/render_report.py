from pathlib import Path
import fitz
root=Path(__file__).resolve().parents[1]
out=root/'output/pdf-preview';out.mkdir(exist_ok=True)
doc=fitz.open(root/'output/piloto-kotosh.pdf')
for i,page in enumerate(doc):
    page.get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(out/f'page-{i+1:02d}.png')
    assert len(page.get_text())>50
print(f'{len(doc)} páginas renderizadas; texto presente en todas.')
