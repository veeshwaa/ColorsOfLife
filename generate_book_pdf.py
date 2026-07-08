import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            # Skip page number on cover page
            return
        self.saveState()
        self.setFont("Times-Italic", 9)
        self.setStrokeColorRGB(0.7, 0.7, 0.7)
        self.setLineWidth(0.5)
        # Draw header rule and running header
        self.line(54, letter[1] - 54, letter[0] - 54, letter[1] - 54)
        self.drawString(54, letter[1] - 48, "Colors of Life")
        
        # Draw footer page number
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 36, page_text)
        self.restoreState()

def compile_book_pdf():
    # Find base dir relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(base_dir, "Colors_of_Life.pdf")
    
    # Chapters map
    chapters = [
        {"dir": "01_The_White_Apron", "title": "CHAPTER I: THE WHITE APRON", "parts": 3},
        {"dir": "02_The_Blue_Collar", "title": "CHAPTER II: THE BLUE COLLAR", "parts": 6},
        {"dir": "03_The_Brown_Chair", "title": "CHAPTER III: THE BROWN CHAIR", "parts": 11},
        {"dir": "04_The_Red_Tea", "title": "CHAPTER IV: THE RED TEA", "parts": 3},
        {"dir": "05_The_Yellow_Envelope", "title": "CHAPTER V: THE YELLOW ENVELOPE", "parts": 3},
        {"dir": "06_The_Green_Lawn", "title": "CHAPTER VI: THE GREEN LAWN", "parts": 5},
        {"dir": "07_Colorless_Tears", "title": "CHAPTER VII: COLORLESS TEARS", "parts": 3}
    ]

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=32,
        leading=38,
        alignment=1, # Center
        spaceAfter=15
    )
    
    author_style = ParagraphStyle(
        'CoverAuthor',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=14,
        leading=18,
        alignment=1, # Center
        spaceAfter=150
    )
    
    chap_style = ParagraphStyle(
        'ChapTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=18,
        leading=22,
        spaceBefore=30,
        spaceAfter=20,
        alignment=0, # Left
        keepWithNext=True
    )
    
    part_style = ParagraphStyle(
        'PartHeader',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=16,
        spaceBefore=15,
        spaceAfter=10,
        alignment=0, # Left
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'NovelBody',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=11,
        leading=15,
        spaceAfter=8,
        alignment=4 # Justify
    )

    story = []

    # Title Page
    story.append(Spacer(1, 150))
    story.append(Paragraph("COLORS OF LIFE", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("A Novel", ParagraphStyle('CoverSub', parent=title_style, fontSize=16, fontName='Times-Italic')))
    story.append(Spacer(1, 40))
    story.append(Paragraph("By Biswa Ranjan Panigrahi", author_style))
    story.append(PageBreak())

    for chap in chapters:
        # Chapter header
        story.append(Paragraph(chap["title"], chap_style))
        story.append(Spacer(1, 5))
        
        for p_idx in range(1, chap["parts"] + 1):
            file_name = f"part-{p_idx}"
            full_path = os.path.join(base_dir, chap["dir"], file_name)
            
            if not os.path.exists(full_path):
                print(f"Warning: file {full_path} not found.")
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Clean up headers like "Part 1" or "Part I" from text to avoid repetition
            lines = content.splitlines()
            if lines and re.match(r'^part\s+\d+', lines[0].strip(), re.IGNORECASE):
                lines = lines[1:]
            
            cleaned_content = "\n".join(lines).strip()
            
            # Mechanical Part Header - Underlined
            story.append(Paragraph(f"<u>PART {p_idx}</u>", part_style))
            
            # Split content by double newlines to form paragraphs
            paragraphs = re.split(r'\n\s*\n', cleaned_content)
            for p_text in paragraphs:
                p_text = p_text.strip()
                if not p_text:
                    continue
                # Escape HTML special chars except basic formatting if any
                p_text = p_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                p_text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', p_text) # translate markdown bold to pdf bold
                
                # Replace back standard HTML escapes if we wanted it
                p_text = p_text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
                p_text = p_text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
                p_text = p_text.replace('&lt;u&gt;', '<u>').replace('&lt;/u&gt;', '</u>')
                
                story.append(Paragraph(f"<i>{p_text}</i>", body_style))
            
            story.append(Spacer(1, 10))
            
        story.append(PageBreak())

    # Build Document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54, # 0.75 in
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF build complete: {pdf_path}")

if __name__ == "__main__":
    compile_book_pdf()
