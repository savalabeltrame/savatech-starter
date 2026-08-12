import os
from fpdf import FPDF
from core.database import get_connection


def gerar_pdf_cupom(numero_cupom, data_venda, itens, total, forma_pagamento, cliente_nome=None):
    conn = get_connection()
    emp = conn.execute("SELECT * FROM config_empresa WHERE id = 1").fetchone()
    conn.close()

    pdf = FPDF()
    pdf.add_page()

    # ===== LOGO Y DATOS DEL CLIENTE =====
    if emp['logo_path'] and os.path.exists(emp['logo_path']):
        pdf.image(emp['logo_path'], x=80, y=8, w=50)
        pdf.ln(28)

    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, emp['nome_empresa'], 0, 1, 'C')
    pdf.set_font('Arial', '', 8)
    if emp['endereco']:
        pdf.cell(0, 4, emp['endereco'], 0, 1, 'C')
    if emp['cnpj'] or emp['telefone']:
        pdf.cell(0, 4, f"CNPJ: {emp['cnpj'] or '-'} | Tel: {emp['telefone'] or '-'}", 0, 1, 'C')
    pdf.set_font('Arial', 'I', 9)
    pdf.cell(0, 5, 'Cupom de Venda - Documento nao fiscal', 0, 1, 'C')
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Cupom N: {numero_cupom}', 0, 1)
    pdf.cell(0, 6, f'Data: {data_venda}', 0, 1)
    if cliente_nome:
        pdf.cell(0, 6, f'Cliente: {cliente_nome}', 0, 1)
    pdf.ln(2)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(90, 6, 'Produto', 0, 0)
    pdf.cell(30, 6, 'Qtd', 0, 0, 'C')
    pdf.cell(40, 6, 'Unit.', 0, 0, 'R')
    pdf.cell(30, 6, 'Total', 0, 1, 'R')
    pdf.set_font('Arial', '', 9)
    for item in itens:
        pdf.cell(90, 6, str(item['nome'])[:32], 0, 0)
        pdf.cell(30, 6, str(item['qtd']), 0, 0, 'C')
        pdf.cell(40, 6, f"{item['unit']:.2f}", 0, 0, 'R')
        pdf.cell(30, 6, f"{item['total']:.2f}", 0, 1, 'R')

    pdf.ln(3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(140, 8, 'TOTAL:', 0, 0, 'R')
    pdf.cell(50, 8, f'R$ {total:.2f}', 0, 1, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Forma de Pagamento: {forma_pagamento}', 0, 1, 'C')
    pdf.ln(4)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 5, 'Obrigado pela sua compra!', 0, 1, 'C')

    return pdf.output()