"""
Search Service - Business Logic for Search Operations

Handles vector search, RAG (Retrieval-Augmented Generation), and graph enrichment.
"""
import logging
from typing import Optional, Iterable

from flask import current_app
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from repositories import QdrantRepository, Neo4jRepository

log = logging.getLogger(__name__)


class SearchService:
    """Service for search operations with vector DB, graph enrichment, and LLM"""

    def __init__(
        self,
        qdrant_repo: QdrantRepository,
        neo4j_repo: Optional[Neo4jRepository],
        embedding_model: Optional[SentenceTransformer] = None,
        llm_client: Optional[OpenAI] = None,
    ):
        """
        Initialize search service.

        Args:
            qdrant_repo: Qdrant repository for vector search
            neo4j_repo: Optional Neo4j repository for graph enrichment
            embedding_model: Optional pre-initialized embedding model
            llm_client: Optional pre-initialized OpenAI client
        """
        self.qdrant_repo = qdrant_repo
        self.neo4j_repo = neo4j_repo
        self._embedding_model = embedding_model
        self._llm_client = llm_client

    def _get_embedding_model(self) -> SentenceTransformer:
        """Lazy-load embedding model"""
        if self._embedding_model is None:
            import os
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            log.info(f"Loading embedding model: {model_name}")
            self._embedding_model = SentenceTransformer(model_name)
        return self._embedding_model

    def _get_llm_client(self) -> OpenAI:
        """Lazy-load OpenAI client"""
        if self._llm_client is None:
            api_key = current_app.config.get("OPENAI_API_KEY")
            if not api_key:
                log.warning("OPENAI_API_KEY not configured - using fallback answer generation")
                return None
            try:
                self._llm_client = OpenAI(api_key=api_key)
            except Exception:
                log.exception("Failed to initialize OpenAI client")
                return None
        return self._llm_client

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
        embeddings = model.encode(texts)
        return embeddings.tolist()

    def vector_search(
        self, query: str, topk: int = 5, collection_name: Optional[str] = None
    ) -> list[dict]:
        """
        Perform vector search on product collection.

        Args:
            query: Search query
            topk: Number of results to return
            collection_name: Optional collection name (uses default if None)

        Returns:
            List of product dictionaries with scores
        """
        if not query:
            return []
            
        col = collection_name or "products"
        
        # 1. Embed query
        query_vector = self.embed_texts([query])[0]
        
        # 2. Search in Qdrant
        results = self.qdrant_repo.search(
            collection_name=col,
            query_vector=query_vector,
            limit=topk,
            with_payload=True
        )
        
        # 3. Format results
        formatted_results = []
        for r in results:
            payload = r.payload or {}
            formatted_results.append({
                "id": r.id,
                "score": r.score,
                "name": payload.get("name", "Unknown"),
                "brand": payload.get("brand", ""),
                "category": payload.get("category", ""),
                "price": payload.get("price", 0.0),
                "document": payload.get("document", "")
            })
            
        return formatted_results

    def rag_search(
        self, strategy: str, query: str, topk: int = 5, use_graph_enrichment: bool = True
    ) -> dict:
        """
        Perform RAG (Retrieval-Augmented Generation) search with graph enrichment.

        Args:
            strategy: Search strategy (not used currently, for compatibility)
            query: Search query
            topk: Number of results to retrieve
            use_graph_enrichment: Whether to enrich results with Neo4j data

        Returns:
            Dictionary with 'query', 'answer', 'hits'
        """
        if not query:
            return {"query": query, "answer": "", "hits": []}

        hits = self.vector_search(query, topk=topk)
        enriched_hits = [dict(hit) for hit in hits]

        if use_graph_enrichment and self.neo4j_repo:
            ids = self._coerce_ints(hit.get("id") for hit in hits)
            if ids:
                enrichment = self.neo4j_repo.get_product_relationships(ids)
                for hit in enriched_hits:
                    hit_id = self._coerce_int(hit.get("id"))
                    if hit_id is None:
                        continue
                    graph_data = enrichment.get(hit_id)
                    if not graph_data:
                        continue
                    if graph_data.get("title"):
                        hit["title"] = graph_data["title"]
                        hit["name"] = graph_data["title"]
                    if graph_data.get("brand"):
                        hit["brand"] = graph_data["brand"]
                    if graph_data.get("category"):
                        hit["category"] = graph_data["category"]
                    if graph_data.get("tags"):
                        hit["tags"] = graph_data["tags"]
                    hit["graph_source"] = "Neo4j"

        answer = self._generate_llm_answer(query, enriched_hits)
        return {"query": query, "answer": answer, "hits": enriched_hits, "strategy": strategy}

    def pdf_rag_search(
        self, query: str, topk: int = 5, pdf_collection: str = "pdf_skripte"
    ) -> Optional[dict]:
        """
        Search in PDF documents with RAG.

        Args:
            query: Search query
            topk: Number of chunks to retrieve
            pdf_collection: PDF collection name

        Returns:
            Dictionary with 'answer' and 'hits', or None on error
        """
        if not query:
            return {"query": query, "answer": "", "hits": [], "collection": pdf_collection}

        query_vector = self.embed_texts([query])[0]
        results = self.qdrant_repo.search(
            collection_name=pdf_collection,
            query_vector=query_vector,
            limit=topk,
            with_payload=True,
        )

        hits: list[dict] = []
        for result in results:
            payload = result.payload or {}
            text = payload.get("text", "")
            page = payload.get("page")
            source = payload.get("source_filename") or payload.get("source") or pdf_collection
            hits.append(
                {
                    "source": source,
                    "page": page,
                    "score": result.score,
                    "text": text,
                    "document": text,
                    "graph_source": None,
                }
            )

        answer = self._generate_pdf_answer(query, hits)
        return {"query": query, "answer": answer, "hits": hits, "collection": pdf_collection}

    def search_product_pdfs(
        self, query: str, topk: int = 3, pdf_products_collection: str = "pdf_produkte"
    ) -> list[dict]:
        """
        Search in product PDF documents.

        Args:
            query: Search query
            topk: Number of chunks to retrieve
            pdf_products_collection: Product PDF collection name

        Returns:
            List of hit dictionaries
        """
        if not query:
            return []

        query_vector = self.embed_texts([query])[0]
        results = self.qdrant_repo.search(
            collection_name=pdf_products_collection,
            query_vector=query_vector,
            limit=topk,
            with_payload=True,
        )

        hits: list[dict] = []
        for result in results:
            payload = result.payload or {}
            text = payload.get("text", "")
            page = payload.get("page")
            source = payload.get("source_filename") or payload.get("source") or pdf_products_collection
            hits.append(
                {
                    "source": source,
                    "page": page,
                    "score": result.score,
                    "text": text,
                    "document": text,
                    "graph_source": None,
                }
            )

        return hits

    def execute_sql_search(self, query: str) -> list[dict]:
        """
        Keyword search via MySQL using parameterized queries.

        Args:
            query: Search term

        Returns:
            List of result dictionaries
        """
        if not query:
            return []
        try:
            from services import ServiceFactory
            product_service = ServiceFactory.get_product_service()
            results = product_service.search_products_by_keyword(keyword=query, limit=20)
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "brand": r.get("brand"),
                    "category": r.get("category"),
                    "price": r.get("price"),
                    "document": r.get("description", ""),
                }
                for r in results
            ]
        except Exception as e:
            log.error(f"Error in SQL search: {e}")
            return []

    def _generate_llm_answer(self, query: str, hits: list[dict]) -> str:
        """
        Generate LLM answer based on search hits.

        Args:
            query: User query
            hits: List of search hits

        Returns:
            LLM-generated answer string
        """
        if not hits:
            return "Keine Treffer gefunden."

        lines = []
        for index, hit in enumerate(hits[:5], start=1):
            title = hit.get("title") or hit.get("name") or "Unbekannt"
            brand = hit.get("brand") or ""
            category = hit.get("category") or ""
            tags = hit.get("tags") or []
            tag_text = ", ".join(tags) if tags else ""
            parts = [f"{index}. {title}"]
            if brand:
                parts.append(f"Marke: {brand}")
            if category:
                parts.append(f"Kategorie: {category}")
            if tag_text:
                parts.append(f"Tags: {tag_text}")
            score = hit.get("score")
            if score is not None:
                parts.append(f"Score: {score:.3f}" if isinstance(score, (int, float)) else f"Score: {score}")
            lines.append(" | ".join(parts))

        client = self._get_llm_client()
        if client is None:
            return (
                "LLM ist nicht konfiguriert. Gefundene Treffer:\n"
                + "\n".join(lines)
            )

        model = current_app.config.get("LLM_MODEL", "gpt-4.1-mini")
        prompt = (
            "Du beantwortest kurze Produktanfragen auf Deutsch. "
            "Nutze nur den gegebenen Kontext und nenne Unsicherheiten offen.\n\n"
            f"Anfrage: {query}\n\n"
            "Kontext:\n"
            + "\n".join(lines)
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Du antwortest präzise und sachlich auf Deutsch."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content if response.choices else None
            if content:
                return content.strip()
        except Exception:
            log.exception("LLM answer generation failed")

        return "LLM-Antwort konnte nicht generiert werden. Gefundene Treffer:\n" + "\n".join(lines)

    def _generate_pdf_answer(self, query: str, hits: list[dict]) -> str:
        """
        Generate an answer for PDF search hits.

        Args:
            query: User query
            hits: PDF hits with source/page/text

        Returns:
            LLM-generated answer or fallback summary
        """
        if not hits:
            return "Keine Treffer in den PDF-Dokumenten gefunden."

        excerpts = []
        for index, hit in enumerate(hits[:5], start=1):
            source = hit.get("source") or "Unbekannt"
            page = hit.get("page") or "?"
            text = (hit.get("text") or "").strip()
            preview = text[:240] + ("..." if len(text) > 240 else "")
            excerpts.append(f"{index}. {source} | Seite {page} | {preview}")

        client = self._get_llm_client()
        if client is None:
            return "LLM ist nicht konfiguriert. Gefundene PDF-Treffer:\n" + "\n".join(excerpts)

        model = current_app.config.get("LLM_MODEL", "gpt-4.1-mini")
        prompt = (
            "Du beantwortest kurze Fragen auf Deutsch anhand von PDF-Ausschnitten. "
            "Nutze nur den gegebenen Kontext und nenne Unsicherheiten offen.\n\n"
            f"Anfrage: {query}\n\n"
            "PDF-Kontext:\n"
            + "\n".join(excerpts)
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Du antwortest präzise und sachlich auf Deutsch."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content if response.choices else None
            if content:
                return content.strip()
        except Exception:
            log.exception("PDF LLM answer generation failed")

        return "PDF-Antwort konnte nicht generiert werden. Gefundene Treffer:\n" + "\n".join(excerpts)

    @staticmethod
    def _coerce_int(value) -> Optional[int]:
        if value is None:
            return None
        try:
            if isinstance(value, bool):
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _coerce_ints(cls, values: Iterable) -> list[int]:
        ints: list[int] = []
        for value in values:
            coerced = cls._coerce_int(value)
            if coerced is not None:
                ints.append(coerced)
        return ints
