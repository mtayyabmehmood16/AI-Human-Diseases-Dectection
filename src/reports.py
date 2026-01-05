from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from datetime import datetime

class PDFReportGenerator:
    def __init__(self, patient):
        self.patient = patient
        self.buffer = io.BytesIO()
        self.styles = getSampleStyleSheet()

    def generate(self):
        doc = SimpleDocTemplate(self.buffer, pagesize=letter)
        elements = []

        # Header
        elements.append(Paragraph(f"Medical Record: {self.patient.name}", self.styles['Title']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

        # Check for Image (Pass if needed using Image(path))
        # if self.patient.image_path: ...

        # Patient Info
        data = [
            ["ID", self.patient.id],
            ["Age", str(self.patient.age)],
            ["Address", self.patient.address],
            ["Risk Profile", "See Online Portal"]
        ]
        t = Table(data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2*inch))

        # Histories
        self._add_section(elements, "Diseases", [d.disease_name for d in self.patient.diseases])
        self._add_section(elements, "Visits", [f"{v.date}: {v.diagnosis or 'Checkup'}" for v in self.patient.visits])
        self._add_section(elements, "Prescriptions", [f"{p.medication} ({p.dosage})" for p in self.patient.prescriptions])

        doc.build(elements)
        self.buffer.seek(0)
        return self.buffer

    def _add_section(self, elements, title, items):
        elements.append(Paragraph(title, self.styles['Heading2']))
        if items:
            for item in items:
                elements.append(Paragraph(f"• {item}", self.styles['Normal']))
        else:
            elements.append(Paragraph("None recorded.", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
