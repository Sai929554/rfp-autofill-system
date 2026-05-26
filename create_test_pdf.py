from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_test_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Draw a table similar to the screenshot
    # Outer box
    c.rect(100, 500, 400, 200)
    # Horizontal lines
    c.line(100, 650, 500, 650) # Below Legal Business Name
    c.line(100, 600, 500, 600) # Below D/B/A
    c.line(100, 550, 500, 550) # Below Signature/Printed Name
    
    # Vertical line for the bottom two rows
    c.line(300, 500, 300, 600)
    
    # Add text
    c.drawString(105, 685, "Legal Business Name of Company Bidding:")
    c.drawString(105, 635, "D/B/A - Doing Business As (if applicable):")
    c.drawString(105, 585, "Bidder's Signature:")
    c.drawString(105, 555, "Title:")
    c.drawString(305, 585, "Printed or Typed Name:")
    c.drawString(305, 555, "Date:")
    c.drawString(105, 535, "Email Address:")
    c.drawString(305, 535, "Phone Number:")
    
    c.save()

if __name__ == "__main__":
    create_test_pdf("test_table.pdf")
    print("Created test_table.pdf")
