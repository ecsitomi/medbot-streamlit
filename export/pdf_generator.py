# =============================================================================
# export/pdf_generator.py
# =============================================================================
"""
PDF generálás az orvosi összefoglalóhoz.
"""
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from .data_formatter import format_field_name, format_field_value

def generate_pdf(export_data):
    """PDF generálása az export adatokból."""
    try:
        pdf_output = BytesIO()
        c = canvas.Canvas(pdf_output, pagesize=A4)
        width, height = A4
        y = height - 20 * mm

        # Címsor
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20 * mm, y, "Egészségügyi Összefoglaló")
        y -= 15 * mm

        # Eset információk
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, f"Eset azonosító: {export_data.get('case_id', 'N/A')}")
        y -= 7 * mm
        c.drawString(20 * mm, y, f"Időpont: {export_data.get('timestamp', 'N/A')}")
        y -= 10 * mm

        # Mezők megjelenítése
        c.setFont("Helvetica", 10)
        for key, value in export_data.items():
            if key in ['case_id', 'timestamp']:
                continue  # Ezeket már megjelenítettük
            
            formatted_key = format_field_name(key)
            formatted_value = format_field_value(value)
            
            text = f"{formatted_key}: {formatted_value}"
            
            # Szöveg tördelése
            max_width = width - 40 * mm
            lines = wrap_text(c, text, max_width, "Helvetica", 10)
            
            for line in lines:
                c.drawString(20 * mm, y, line)
                y -= 5 * mm
                if y < 20 * mm:
                    c.showPage()
                    y = height - 20 * mm
                    c.setFont("Helvetica", 10)

        c.save()
        pdf_output.seek(0)
        return pdf_output
    except Exception as e:
        st.error(f"Hiba a PDF generálásában: {e}")
        return None

def wrap_text(canvas_obj, text, max_width, font_name, font_size):
    """Szöveg tördelése a megadott szélességhez."""
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if canvas_obj.stringWidth(test_line, font_name, font_size) < max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

def create_advanced_pdf(export_data):
    """Fejlettebb PDF generálás szekciókkal."""
    try:
        pdf_output = BytesIO()
        c = canvas.Canvas(pdf_output, pagesize=A4)
        width, height = A4
        y = height - 20 * mm

        # Fejléc
        c.setFont("Helvetica-Bold", 18)
        c.drawString(20 * mm, y, "Egészségügyi Összefoglaló")
        y -= 20 * mm

        # Eset információk
        _draw_section(c, "Eset információk", y, width)
        y -= 10 * mm
        y = _draw_key_value(c, "Eset azonosító", export_data.get('case_id', 'N/A'), y)
        y = _draw_key_value(c, "Időpont", export_data.get('timestamp', 'N/A'), y)
        y -= 5 * mm

        # Páciens adatok
        if y < 50 * mm:
            c.showPage()
            y = height - 20 * mm
        
        _draw_section(c, "Páciens adatok", y, width)
        y -= 10 * mm
        y = _draw_key_value(c, "Életkor", f"{export_data.get('age', 'N/A')} év", y)
        y = _draw_key_value(c, "Nem", export_data.get('gender', 'N/A'), y)
        y = _draw_key_value(c, "Tünetek", format_field_value(export_data.get('symptoms', [])), y)
        y = _draw_key_value(c, "Időtartam", export_data.get('duration', 'N/A'), y)
        y = _draw_key_value(c, "Súlyosság", export_data.get('severity', 'N/A'), y)
        y -= 5 * mm

        # Orvosi értékelés
        if y < 50 * mm:
            c.showPage()
            y = height - 20 * mm
        
        _draw_section(c, "Orvosi értékelés", y, width)
        y -= 10 * mm
        y = _draw_key_value(c, "Triage szint", export_data.get('triage_level', 'N/A'), y)
        y = _draw_key_value(c, "Diagnózis", export_data.get('diagnosis', 'N/A'), y)
        y = _draw_key_value(c, "Javasolt szakorvos", export_data.get('specialist', 'N/A'), y)
        
        c.save()
        pdf_output.seek(0)
        return pdf_output
    except Exception as e:
        st.error(f"Hiba a fejlett PDF generálásában: {e}")
        return None

def _draw_section(canvas_obj, title, y, width):
    """Szekció címének rajzolása."""
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(20 * mm, y, title)
    # Vonal húzása a cím alá
    canvas_obj.line(20 * mm, y - 2 * mm, width - 20 * mm, y - 2 * mm)

def _draw_key_value(canvas_obj, key, value, y):
    """Kulcs-érték pár rajzolása."""
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawString(20 * mm, y, f"{key}:")
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawString(60 * mm, y, str(value))
    return y - 6 * mm