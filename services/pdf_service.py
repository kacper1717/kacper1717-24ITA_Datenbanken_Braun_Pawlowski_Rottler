"""
PDF Service - Business Logic for PDF Upload and Management

Handles PDF upload, chunking, and indexing into Qdrant.
"""
import logging
from typing import Optional

from flask import current_app
from sentence_transformers import SentenceTransformer
from werkzeug.utils import secure_filename

from repositories import QdrantRepository

log = logging.getLogger(__name__)

# Collection names
COLLECTION_PDF = "pdf_skripte"
COLLECTION_PDF_PRODUCTS = "pdf_produkte"


class PDFService:
    """Service for PDF upload and management"""

    def __init__(
        self,
        qdrant_repo: QdrantRepository,
        embedding_model: Optional[SentenceTransformer] = None,
    ):
        """
        Initialize PDF service.

        Args:
            qdrant_repo: Qdrant repository for vector operations
            embedding_model: Optional pre-initialized embedding model
        """
        self.qdrant_repo = qdrant_repo
        self._embedding_model = embedding_model

    def _get_embedding_model(self) -> SentenceTransformer:
        """Lazy-load embedding model"""
        if self._embedding_model is None:
            model_name = current_app.config.get(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            )
            log.info("Loading PDF embedding model: %s", model_name)
            self._embedding_model = SentenceTransformer(model_name)
        return self._embedding_model

    def embed_texts(self, texts: list[str]) -> list:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (numpy arrays)
        """
        if not texts:
            return []
        model = self._get_embedding_model()
        return model.encode(texts).tolist()

    def _get_vector_size(self) -> int:
        return int(current_app.config.get("EMBEDDING_DIM", 384))

    def _ensure_collection(self, collection_name: str) -> None:
        self.qdrant_repo.ensure_collection(
            collection_name=collection_name,
            vector_size=self._get_vector_size(),
        )

    @staticmethod
    def _safe_filename(pdf_file) -> str:
        original = getattr(pdf_file, "filename", None) or "upload.pdf"
        return secure_filename(original) or "upload.pdf"

    def _upload_pdf(self, pdf_file, collection_name: str, chunk_size: int = 300) -> str:
        filename = self._safe_filename(pdf_file)
        chunks = self.qdrant_repo.extract_pdf_chunks(pdf_file, chunk_size=chunk_size)
        if not chunks:
            return f"Keine verwertbaren Texte in {filename} gefunden."

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embed_texts(texts)
        if not embeddings:
            return f"Konnte keine Embeddings für {filename} erzeugen."

        self._ensure_collection(collection_name)
        uploaded = self.qdrant_repo.upload_pdf_chunks(
            collection_name=collection_name,
            chunks=chunks,
            embeddings=embeddings,
            source_filename=filename,
        )
        return f"{filename} erfolgreich indexiert: {uploaded} Chunks in {collection_name}."

    def upload_pdf_to_qdrant(
        self, pdf_file, collection_name: str = COLLECTION_PDF, chunk_size: int = 300
    ) -> str:
        """
        Upload a teaching PDF to Qdrant.

        Args:
            pdf_file: File object (Flask request.files)
            collection_name: Target collection name
            chunk_size: Size of text chunks in characters

        Returns:
            Status message string

        Raises:
            Exception: On upload errors
        """
        if pdf_file is None:
            raise ValueError("Keine PDF-Datei übergeben.")
        return self._upload_pdf(pdf_file, collection_name=collection_name, chunk_size=chunk_size)

    def upload_product_pdf(self, pdf_file, chunk_size: int = 300) -> str:
        """
        Upload a product PDF to Qdrant.

        Args:
            pdf_file: File object (Flask request.files)
            chunk_size: Size of text chunks in characters

        Returns:
            Status message string

        Raises:
            Exception: On upload errors
        """
        if pdf_file is None:
            raise ValueError("Keine Produktkatalog-PDF übergeben.")
        return self._upload_pdf(pdf_file, collection_name=COLLECTION_PDF_PRODUCTS, chunk_size=chunk_size)

    def get_pdf_counts(self) -> dict:
        """
        Get count of unique PDF files in both collections.

        Returns:
            Dictionary with counts for teaching and product PDFs
        """
        return {
            "pdf_skripte": len(self.list_teaching_pdfs()),
            "pdf_produkte": len(self.list_product_pdfs()),
            "total": len(self.list_teaching_pdfs()) + len(self.list_product_pdfs()),
        }

    def list_uploaded_pdfs(
        self, collection_name: Optional[str] = None
    ) -> list[str]:
        """
        List all uploaded PDF filenames.

        Args:
            collection_name: Optional collection name (defaults to teaching PDFs)

        Returns:
            Sorted list of unique PDF filenames
        """
        collection = collection_name or COLLECTION_PDF
        self.ensure_collections()
        return self.qdrant_repo.list_uploaded_pdfs(collection)

    def list_teaching_pdfs(self) -> list[str]:
        """
        List all teaching PDFs.

        Returns:
            Sorted list of teaching PDF filenames
        """
        return self.list_uploaded_pdfs(COLLECTION_PDF)

    def list_product_pdfs(self) -> list[str]:
        """
        List all product PDFs.

        Returns:
            Sorted list of product PDF filenames
        """
        return self.list_uploaded_pdfs(COLLECTION_PDF_PRODUCTS)

    def ensure_collections(self) -> None:
        """
        Ensure both PDF collections exist.

        Creates the collections if they don't exist yet.
        """
        self._ensure_collection(COLLECTION_PDF)
        self._ensure_collection(COLLECTION_PDF_PRODUCTS)

    def get_collection_stats(self, collection_name: Optional[str] = None) -> dict:
        """
        Get statistics for a PDF collection.

        Args:
            collection_name: Optional collection name (defaults to teaching PDFs)

        Returns:
            Dictionary with collection statistics
        """
        collection = collection_name or COLLECTION_PDF
        self.ensure_collections()
        info = self.qdrant_repo.get_collection_info(collection)
        info["sources"] = self.list_uploaded_pdfs(collection)
        info["source_count"] = len(info["sources"])
        return info