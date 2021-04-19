import time
import random
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4, portrait
from reportlab.platypus import BaseDocTemplate, PageTemplate, Paragraph, Spacer, Image, Frame, FrameBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import utils

from . import util
from . import config as cf

def get_image(path, width=1*cm):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))


def generate_report(**kwargs):

    util.generate_barcode(cf.barcode_string.format(order_number=kwargs["order_number"]))

    doc = BaseDocTemplate(
        'form.pdf',
        title='Return / Exchange Form',
        showBoundary=0,
        pagesize=portrait(A4),
        topMargin=10,
        bottomMargin=10,
        leftMargin=20,
        rightMargin=20)

    frameCount = 1
    frameWidth = doc.width / frameCount
    frameHeight = doc.height - 2*inch

    headerFrameWidth = doc.width

    frame_list = [
        Frame(
            x1=doc.leftMargin,
            y1=doc.height-2*inch,
            width=doc.width,
            height=150),
        Frame(
            x1=doc.leftMargin,
            y1=doc.height-4.1*inch,
            width=200,
            height=150),
        Frame(
            x1=doc.width - 2.25*inch,
            y1=doc.height-4.1*inch,
            width=200,
            height=150),
        Frame(
            x1=doc.leftMargin,
            y1=doc.height - 7.9*inch,
            width=doc.width,
            height=275),
        Frame(
            x1=doc.leftMargin,
            y1=doc.height - 11*inch,
            width=doc.width,
            height=200),
    ]

    doc.addPageTemplates([PageTemplate(id='frames', frames=frame_list), ])

    story = []

    user_info = [
        ("Name: ", kwargs["name"]),
        ("Address: ", kwargs["address"]),
        ("City: ", kwargs["city"]),
        ("Country Area: ", kwargs["country_area"]),
#        ("Country: ", kwargs["country"]),
        ("Zip: ", kwargs["zipcode"]),
        ("Email: ", kwargs["email"]),
#        ("Phone: ", kwargs["phone"])
    ]

    story.append(get_image(cf.logo, width=8*cm))

    styles=getSampleStyleSheet()

    title_style = styles['Heading2']
    title_style.alignment = 1
    title = Paragraph("Return / Exchange Form", title_style)
    story.append(title)

    order_number_style = styles['Heading2']
    order_number_style.alignment = 1
    htext = '<font size="14">%s</font>' % ("Order #" + kwargs["order_number"])
    story.append(Paragraph(htext, order_number_style))
    story.append(Spacer(1, 12))

    for i in range(len(user_info)):
        ptext = '<font size="11">%s</font>' % (user_info[i][0] + user_info[i][1])
        story.append(Paragraph(ptext, styles["Normal"]))
        story.append(Spacer(1, 10))

    story.append(get_image(cf.barcode, width=6*cm))

    story.append(Spacer(1, 8))

    for i in cf.info_dict:
        ptext = '<font size="11">%s</font>' % (cf.info_dict[i])
        story.append(Paragraph(ptext, styles["Normal"]))
        story.append(Spacer(1, 12))

    footer_style = styles["Heading4"]
    footer_style.alignment = 1
    ptext = '<font size="11">%s</font>' % (cf.instruction)
    story.append(Paragraph(ptext, footer_style))
    story.append(HRFlowable(width="100%", thickness=1, color="#707070"))

    story.append(Spacer(1, 12))

    for i in range(len(cf.shipto_address)):
        ptext = '<font size="11">%s</font>' % (cf.shipto_address[i])
        story.append(Paragraph(ptext, footer_style))

    ptext = '<font size="11">%s</font>' % ("Order #" + kwargs["order_number"])
    story.append(Paragraph(ptext, footer_style))

    doc.build(story)
