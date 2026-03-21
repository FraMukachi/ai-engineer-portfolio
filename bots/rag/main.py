import os
import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class RAGBot:
    """Bot that answers questions using business documents"""
    
    def __init__(self):
        self.knowledge_base = {}  # business_id -> documents
    
    async def add_knowledge(self, business_id: str, document: Dict[str, Any]):
        """Add document to business knowledge base"""
        if business_id not in self.knowledge_base:
            self.knowledge_base[business_id] = []
        
        self.knowledge_base[business_id].append(document)
        logger.info(f"Added knowledge for {business_id}")
    
    async def query(self, business_id: str, question: str) -> Dict[str, Any]:
        """Answer question using business documents"""
        try:
            if business_id not in self.knowledge_base:
                return {"response": "No documents uploaded yet. Please upload business documents first."}
            
            # Simple keyword matching (will be enhanced with embeddings later)
            docs = self.knowledge_base[business_id]
            relevant_docs = self._find_relevant_docs(docs, question)
            
            if not relevant_docs:
                return {"response": "I couldn't find information about that in your documents."}
            
            # Generate response from relevant documents
            response = self._generate_response(question, relevant_docs)
            
            return {
                "response": response,
                "sources": [d.get("filename", "Unknown") for d in relevant_docs[:3]]
            }
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"error": str(e)}
    
    def _find_relevant_docs(self, docs: List[Dict], question: str) -> List[Dict]:
        # Simple relevance scoring (will be replaced with embeddings)
        question_lower = question.lower()
        scored_docs = []
        
        for doc in docs:
            score = 0
            content = doc.get("content", "").lower()
            if content:
                # Count keyword matches
                keywords = question_lower.split()
                for keyword in keywords:
                    if keyword in content:
                        score += content.count(keyword)
            
            if score > 0:
                scored_docs.append((score, doc))
        
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        return [doc for score, doc in scored_docs[:3]]
    
    def _generate_response(self, question: str, relevant_docs: List[Dict]) -> str:
        # Simple response generation (will be enhanced with Groq)
        sources = [doc.get("filename", "Document") for doc in relevant_docs]
        
        if "menu" in question.lower():
            return "Based on your menu, we offer various items. Please specify what you're looking for."
        elif "price" in question.lower():
            return "I can help with pricing information. What specific item are you interested in?"
        elif "book" in question.lower() or "appointment" in question.lower():
            return "I can help book an appointment. What date and time would you prefer?"
        
        return f"I found information in {', '.join(sources)}. What specific details would you like to know?"

# Singleton instance
rag_bot = RAGBot()
