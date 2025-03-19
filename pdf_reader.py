import pdfplumber
import fitz  # PyMuPDF


class PDFReader:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.pdf = None
        self.page_count = 0
        self.library = None

        # Try pdfplumber first
        try:
            self.pdf = pdfplumber.open(pdf_path)
            self.page_count = len(self.pdf.pages)
            self.library = 'pdfplumber'
        except Exception as e:
            print(f"Error with pdfplumber: {e}")
            self.library = None

        # Fallback to PyMuPDF if pdfplumber fails
        if not self.library:
            try:
                self.pdf = fitz.open(pdf_path)
                self.page_count = self.pdf.page_count
                self.library = 'PyMuPDF'
            except Exception as e:
                print(f"Error with PyMuPDF: {e}")
                self.library = None

        if self.library:
            print(f"Using {self.library} to process the PDF.")
        else:
            print("No suitable library found to open the PDF.")

    def get_page_count(self):
        return self.page_count

    def get_page_text_lines(self, page_number):
        if self.library == 'pdfplumber':
            return self._get_page_text_plumber(page_number)
        elif self.library == 'PyMuPDF':
            return self._get_page_text_fitz(page_number)
        else:
            return []

    def _get_page_text_plumber(self, page_number):
        """ Extracts line-by-line text using pdfplumber """
        if page_number < 0 or page_number >= self.page_count:
            raise ValueError("Page number out of range.")
        # print(page_number)
        page = self.pdf.pages[page_number]
        text = page.extract_text()
        # print(page)
        if text:
            return text.split('\n')
        return []

    def _get_page_text_fitz(self, page_number):
        """ Extracts line-by-line text using PyMuPDF """
        if page_number < 0 or page_number >= self.page_count:
            raise ValueError("Page number out of range.")

        page = self.pdf.load_page(page_number)
        text = page.get_text("text")  # 'text' extracts plain text
        if text:
            return text.split('\n')
        return []




if __name__ == "__main__":
# Example usage:
    pdf_path = 'Material/Document.pdf'

    # Create a PDFReader object
    pdf_reader = PDFReader(pdf_path)

    # Get page count
    page_count = pdf_reader.get_page_count()
    print(f"Total Pages: {page_count}")

    # Get line-by-line text for a specific page (e.g., page 1)
    page_number = 1154
    lines = pdf_reader.get_page_text_lines(page_number)
    for line in lines:
        print(line)
