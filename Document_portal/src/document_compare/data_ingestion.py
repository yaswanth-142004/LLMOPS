from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
import sys
from pathlib import Path
import fitz


class DocumentIngestion:
    def __init__(self,base_dir):
      self.log = CustomLogger().get_logger(__name__)
      self.base_dir = Path(base_dir)
      self.base_dir.mkdir(parents=True,exist_ok=True)


    def delete_existing_files(self):

      try:
        pass
      catch Exception  as e:
        self.log.error(f"Error deleting existing files: {e}")
        rasie DocumentPortalException("An Error  occured while deleting existing files",sys)


    def save_uploaded_files(self):
      """Save uploaded files in  a specific directory
      """
      try:
        pass
      catch Exception  as e:
        self.log.error(f"Error saving uploaded files: {e}")
        rasie DocumentPortalException("An Error  occured while saving uploaded files",sys)


      def read_pdf(self,pdf_path:Path)->str:
        """Reads a pdf and extracts text from each page

        Args:
            pdf_path (Path): _description_

        Returns:
            str: _description_
        """
        try:
          with fitz.open(pdf_path) as doc:
            if doc.is_encrypted:
              raise ValueError("PDF is encrypted and cannot be read :{pdf_path.name}")

            all_text = []

            for page_num in range(doc.page_count):
              page = doc.load_page(page_num)
              text = page.get_text()
              if text.strip():
                all_text.append(f"\n -----Page{page_num  +1}-----\n{text}")
            self.log.info(f"Extracted text from {pdf_path.name} succesfully")
            return "\n".join(all_text)
        except Exception as e:
          self.log.error(f"Error reading PDF {pdf_path.name}: {e}")
          raise DocumentPortalException(f"An error occured while reading PDF {pdf_path.name}",sys)
