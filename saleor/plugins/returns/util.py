import barcode
from barcode.writer import ImageWriter

def generate_barcode(string):
    code128 = barcode.get('code128', string, writer=ImageWriter())
    filename = code128.save('code128')
