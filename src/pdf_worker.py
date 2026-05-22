from PyQt6.QtCore import QThread, pyqtSignal

class PDFWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, html_string, output_file):
        super().__init__()
        self.html_string = html_string
        self.output_file = output_file

    def run(self):
        try:
            from weasyprint import HTML
            HTML(string=self.html_string).write_pdf(self.output_file)
            self.finished.emit(self.output_file)
        except Exception as e:
            self.error.emit(str(e))