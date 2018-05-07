from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from html import escape as html_escape
import markdown


class NotebookConverter():
    def __init__(self, filename):
        import json
        with open(filename) as fp:
            self.book = json.load(fp)

    def to_html(self, with_body=True, stylesheet="css/style.css"):
        html = []
        for cell in self.book["cells"]:
            if cell["cell_type"] == "markdown":
                md = "".join(cell["source"])
                if md:
                    html.append(markdown.markdown(md.strip()))
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                if source and "NotebookConverter" not in source:
                    html.append(self.python_to_html(source))
            if cell.get("outputs"):
                for output in cell["outputs"]:
                    if "text/html" in output.get("data", {}):
                        outp = "".join(output["data"]["text/html"])
                        if outp:
                            html.append(self._fix_html(outp))
                    elif "text/plain" in output.get("data", {}):
                        outp = "".join(output["data"]["text/plain"])
                        if outp:
                            html.append('<div class="output"><pre>%s</pre></div>' % html_escape(outp))
                    if "text" in output:
                        outp = "".join(output["text"])
                        if outp:
                            html.append('<div class="output"><pre>%s</pre></div>' % html_escape(outp))
                    #print("------", output)

        html = "\n".join("<!-- output #%s -->\n%s\n" % t for t in enumerate(html))
        if with_body:
            html = """
            <!doctype html>
            <html>
                <head profile="http://www.w3.org/2005/10/profile">
                    <meta charset="utf-8">
                    <link href="css/highlight.css" rel="stylesheet" type="text/css" />
                    <link href="%s" rel="stylesheet" type="text/css" />
                </head>
            
                <body>
                    %s    
                </body>
            </html>""" % (stylesheet, html)
        return html

    def to_html_file(self, filename, **kwargs):
        with open(filename, "wt") as fp:
            fp.write(self.to_html(**kwargs))

    @classmethod
    def _fix_html(cls, h):
        return h
        if '<style' in h:
            h = h[:h.index('<style')] + h[h.index("</style>")+8:]
        return h

    @classmethod
    def python_to_html(cls, code):
        lexer = get_lexer_by_name("python")
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)


