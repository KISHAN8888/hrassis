import os, logging, tempfile, shutil
from app.utils.http_responses import Responses
logging.basicConfig(level=logging.INFO)

class TempFolder:
    @staticmethod
    async def create_temp_folder(file):
        "Create a temporary folder for the uploaded file"
        suffix = os.path.splitext(file.filename)[1]
        logging.info("Creating temporary folder for file: %s", file.filename)
        temp_file_name = None
        try:
            with tempfile.TemporaryDirectory(delete=False, suffix=suffix) as temp_dir:
                content = await file.read()
                temp_dir.write(content)
                temp_dir.flush()
                temp_file_name = temp_dir.name
                logging.info("Temporary folder created: %s", temp_file_name)
                return temp_file_name
            
        except Exception as e:
            logging.error("Error creating temporary folder: %s", str(e))
            if temp_file_name:
                shutil.rmtree(temp_file_name)
            return Responses.error(500, message="Error creating temporary folder")
        
    @staticmethod
    async def delete_temp_folder(temp_file_name):
        "Delete the temporary folder"
        logging.info("Deleting temporary folder: %s", temp_file_name)
        try:
            shutil.rmtree(temp_file_name)
            logging.info("Temporary folder deleted: %s", temp_file_name)
        except Exception as e:
            logging.error("Error deleting temporary folder: %s", str(e))
            return Responses.error(500, message="Error deleting temporary folder")
            
            