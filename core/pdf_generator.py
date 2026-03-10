from fpdf import FPDF
import os
from core import db

class DossierPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Dossier Estructural MisSocios24/7', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_dossier(telegram_id):
    adn = db.obtener_adn_completo(telegram_id)
    nombre_usuario = adn.get('nombre_completo', 'Socio')
    empresa = adn.get('nombre_empresa', 'N/A')
    rubro = adn.get('rubro', 'N/A')
    dolor = adn.get('dolor_principal', 'N/A')
    equipo = adn.get('equipo', [])
    
    pdf = DossierPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(0, 10, f'Resumen para: {nombre_usuario}', 0, 1, 'L', 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Información del Negocio', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, f"Empresa: {empresa}\nRubro: {rubro}\nDolor Detectado: {dolor}")
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Tu Mesa Directiva Personalizada', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    for agente in equipo:
        txt = f"- {agente['nombre_agente']} ({agente['rol_socket']})\n"
        txt += f"  Personalidad: {agente['personality']}\n" if 'personality' in agente else f"  Personalidad: {agente.get('personalidad', 'N/A')}\n"
        txt += f"  Liderazgo: {agente.get('estilo_liderazgo', 'N/A')}\n"
        pdf.multi_cell(0, 5, txt)
        pdf.ln(2)

    # VERA-027: Mapa del Proyecto
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Plan de Inteligencia Estructural (12 Semanas)', 0, 1)
    pdf.set_font('Arial', '', 10)
    mapa = """Fase 1: Auditoría y ADN (Semanas 1-3)
Fase 2: Arquitectura de Producto (Semanas 4-6)
Fase 3: Optimización Financiera (Semanas 7-9)
Fase 4: Escalabilidad y Narrativa (Semanas 10-12)"""
    pdf.multi_cell(0, 5, mapa)

    # VERA-027: QR Mock de Pago
    pdf.ln(10)
    pdf.set_draw_color(0, 0, 0)
    pdf.rect(pdf.get_x(), pdf.get_y(), 30, 30)
    pdf.set_xy(pdf.get_x() + 35, pdf.get_y())
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, 'PAGAR SUBSCRIPCIÓN (QR MOCK)', 0, 1)
    pdf.set_xy(pdf.get_x() + 35, pdf.get_y() - 15)
    pdf.set_font('Arial', '', 8)
    pdf.cell(0, 10, 'Escanea para activar la Fase 1', 0, 1)
    
    path = os.path.join('c:/tmp', f"Dossier_Estructural_{telegram_id}.pdf")
    pdf.output(path)
    return path
