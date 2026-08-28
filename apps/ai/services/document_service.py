import os
import json
import logging
from typing import Tuple, Optional, List, Dict, Any
from django.core.files.uploadedfile import UploadedFile
from common.enums import KnowledgeDocumentStatus, KnowledgeSourceType
from ..models import KnowledgeDocument, DocumentChunk

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """
    Handles text extraction, preprocessing, and document lifecycle for Knowledge Base documents.
    """

    SUPPORTED_TEXT_EXTENSIONS = {
        "txt", "md", "markdown", "csv", "json", "jsonl",
        "html", "htm", "xml", "log", "rst", "tsv", "yaml", "yml"
    }

    @classmethod
    def extract_text_from_file(cls, uploaded_file: UploadedFile) -> Tuple[str, str, int]:
        """
        Extracts plain text content, detected extension, and byte size from an uploaded file.
        Returns:
            Tuple[str, str, int]: (extracted_text, file_type, file_size)
        """
        file_name = uploaded_file.name or "uploaded_file"
        file_size = uploaded_file.size
        ext = os.path.splitext(file_name)[1].lower().lstrip(".")

        extracted_text = ""

        try:
            # Read file bytes
            uploaded_file.seek(0)
            file_bytes = uploaded_file.read()

            # Attempt UTF-8 decoding
            try:
                extracted_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to latin-1 with error ignoring
                extracted_text = file_bytes.decode("latin-1", errors="ignore")

            # Reset file pointer for storage saving
            uploaded_file.seek(0)

        except Exception as e:
            logger.warning("Failed to extract text from file %s: %s", file_name, str(e))
            extracted_text = ""

        return extracted_text, ext, file_size

    @classmethod
    def create_document_from_upload(
        cls,
        organization,
        user,
        file: Optional[UploadedFile] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        raw_content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_type: Optional[str] = None,
        is_active: bool = True
    ) -> KnowledgeDocument:
        """
        Creates a new KnowledgeDocument record from an uploaded file or raw text input.
        """
        tags = tags or []
        metadata = metadata or {}

        file_name = None
        file_type = None
        file_size = None
        extracted_text = raw_content or ""

        if file:
            file_name = file.name
            extracted_text, file_type, file_size = cls.extract_text_from_file(file)
            if not source_type:
                source_type = KnowledgeSourceType.FILE
            if not title:
                title = os.path.splitext(file.name)[0]
        else:
            if not source_type:
                source_type = KnowledgeSourceType.TEXT

        if not title:
            title = "Untitled Document"

        char_count = len(extracted_text) if extracted_text else 0
        word_count = len(extracted_text.split()) if extracted_text else 0

        document = KnowledgeDocument.objects.create(
            organization=organization,
            title=title,
            description=description,
            file=file,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            source_type=source_type,
            raw_content=extracted_text,
            status=KnowledgeDocumentStatus.PENDING,
            character_count=char_count,
            word_count=word_count,
            tags=tags,
            metadata=metadata,
            is_active=is_active,
            created_by=user
        )

        return document
