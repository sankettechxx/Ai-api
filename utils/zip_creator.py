import os
import zipfile
import tempfile
from datetime import datetime

class ZipCreator:
    @staticmethod
    def create(files_dict):
        """Create ZIP from dict of {filename: content}"""
        temp_dir = tempfile.mkdtemp()
        zip_name = f'code_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        zip_path = os.path.join(temp_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files_dict.items():
                filepath = os.path.join(temp_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                zf.write(filepath, filename)
        
        return zip_path
    
    @staticmethod
    def add_folder(zip_obj, folder_path, arcname_prefix=''):
        """Recursively add folder to ZIP"""
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.join(arcname_prefix, os.path.relpath(filepath, folder_path))
                zip_obj.write(filepath, arcname)