import PyPDF2,mammoth,requests,logging
from io import BytesIO
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)

class ResumeHelper:
    """Helper class for resume text extraction and processing"""
    
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract text content from a PDF file"""
        try:
            text = []
            with BytesIO(file_bytes) as file:
                reader = PyPDF2.PdfReader(file)
                for _, page in enumerate(reader.pages):
                    extracted = page.extract_text()
                    if extracted:
                        text.append(extracted)
            if not text:
                logging.warning("No text content extracted from PDF")
                return ""
            return '\n'.join(text)
        except Exception as e:
            logging.error("Error extracting text from PDF: %s", str(e))
            return ""
    
    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extract text content from a DOCX file"""
        try:
            with BytesIO(file_bytes) as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                text = result.value
                if not text:
                    logging.warning("No text content extracted from DOCX")
                return text
        except Exception as e:
            logging.error("Error extracting text from DOCX: %s", str(e))
            return ""
        
    @staticmethod
    def extract_text_from_file_path(file_path: str) -> Optional[str]:
        """Extract text from a resume file based on its extension"""

        logging.info("Extracting bytes from file path: %s", file_path)
        response = requests.get(file_path, stream=True)
        file_bytes = response.content
        
        
        if file_path.lower().endswith('.docx'):
            resume_text = ResumeHelper.extract_text_from_docx(file_path)
        elif file_path.lower().endswith('.pdf'):
            resume_text = ResumeHelper.extract_text_from_pdf(file_bytes)
        else:
            logging.warning("Unsupported file type: %s", file_path)
            return None

        if not resume_text:
            logging.warning("No text extracted from %s", file_path)
            return None
        return resume_text
    
    @staticmethod
    def calculate_overall_score(attribute_scores: Dict, weightage_dict: Dict) -> float:
        """Calculate the overall score for a candidate based on attribute scores and weightage."""
        try:
            overall_score = (
                attribute_scores['skills_score'] * weightage_dict.get('skills_score', 25) +
                attribute_scores['experience_score'] * weightage_dict.get('experience_score', 25) +
                attribute_scores['qualifications_score'] * weightage_dict.get('qualifications_score', 25) +
                attribute_scores['relatedProjects_score'] * weightage_dict.get('project_score', 25)
            ) / 100
            return overall_score
        except Exception as e:
            logging.error("Error calculating overall score: %s", str(e))
            return 0.0
