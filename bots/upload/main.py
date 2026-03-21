import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DocumentUploadBot:
    """Bot that handles document uploads and processing"""
    
    def __init__(self, data_dir: str = "data/documents"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def upload_document(self, business_id: str, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload and store a document for a business"""
        try:
            # Create business directory
            business_dir = self.data_dir / business_id
            business_dir.mkdir(exist_ok=True)
            
            # Save file
            file_id = str(uuid.uuid4())
            file_path = business_dir / f"{file_id}_{filename}"
            
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Process document based on type
            doc_info = {
                "id": file_id,
                "filename": filename,
                "path": str(file_path),
                "size": len(file_content),
                "type": self._get_document_type(filename),
                "uploaded_at": "2026-03-21"
            }
            
            logger.info(f"Document uploaded: {doc_info}")
            return doc_info
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return {"error": str(e)}
    
    def _get_document_type(self, filename: str) -> str:
        ext = filename.split('.')[-1].lower()
        if ext in ['pdf']:
            return 'pdf'
        elif ext in ['docx', 'doc']:
            return 'word'
        elif ext in ['txt']:
            return 'text'
        elif ext in ['jpg', 'png']:
            return 'image'
        return 'unknown'
    
    def list_documents(self, business_id: str) -> list:
        business_dir = self.data_dir / business_id
        if not business_dir.exists():
            return []
        
        docs = []
        for file in business_dir.iterdir():
            docs.append({
                "id": file.name.split('_')[0],
                "filename": '_'.join(file.name.split('_')[1:]),
                "path": str(file)
            })
        return docs

# Singleton instance
upload_bot = DocumentUploadBot()
