from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.formatters import HtmlFormatter
from html import escape as html_escape
import markdown


class NotebookConverter():
    def __init__(self, filename):
        import json
        with open(filename) as fp:
            self.book = json.load(fp)

    def to_html(self):
        html = []
        for cell in self.book["cells"]:
            if cell["cell_type"] == "markdown":
                html.append(markdown.markdown(" ".join(cell["source"])))
            if cell["cell_type"] == "code":
                html.append(self.python_to_html(" ".join(cell["source"])))
            if cell.get("outputs"):
                for output in cell["outputs"]:
                    if "text/html" in output.get("data", {}):
                        html.append( " ".join(output["data"]["text/html"]) )
                    if "text" in output:
                        html.append( "<pre>%s</pre>" % html_escape(" ".join(output["text"])) )
                    #else:
                    #    print("------", output)
        return "\n".join("<!-- cell #%s -->\n%s\n" % t for t in enumerate(html))

    @classmethod
    def python_to_html(cls, code):
        lexer = get_lexer_by_name("python")
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)


