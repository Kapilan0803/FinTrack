import io
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict={}):
    """
    Renders an HTML template into a PDF document using xhtml2pdf.
    Safe, robust, and works 100% on Windows without external GTK libraries.
    """
    html = render_to_string(template_src, context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None
