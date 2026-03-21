import os
import json
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AnalysisBot:
    """Bot that analyzes documents and extracts structured data"""
    
    def __init__(self):
        self.extraction_patterns = {
            "phone": r'(\+?27|0)[0-9]{9}',
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "price": r'R\s?\d+(?:\.\d{2})?',
            "time": r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',
            "date": r'\d{1,2}\/\d{1,2}\/\d{2,4}'
        }
    
    async def analyze_document(self, content: str, doc_type: str) -> Dict[str, Any]:
        """Extract structured information from documents"""
        try:
            analysis = {
                "entities": self._extract_entities(content),
                "summary": self._generate_summary(content),
                "key_points": self._extract_key_points(content),
                "intent": self._detect_intent(content),
                "actions": self._detect_actions(content)
            }
            
            logger.info(f"Document analysis complete: {analysis['summary']}")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"error": str(e)}
    
    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        entities = {}
        for entity_type, pattern in self.extraction_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                entities[entity_type] = list(set(matches))
        return entities
    
    def _generate_summary(self, content: str) -> str:
        # Simple summary - first 200 chars
        return content[:200] + "..."
    
    def _extract_key_points(self, content: str) -> List[str]:
        # Extract sentences that might be key points
        sentences = re.split(r'[.!?]+', content)
        key_points = [s.strip() for s in sentences if len(s.strip()) > 30][:5]
        return key_points
    
    def _detect_intent(self, content: str) -> str:
        content_lower = content.lower()
        if any(word in content_lower for word in ['menu', 'food', 'drink']):
            return "restaurant_menu"
        elif any(word in content_lower for word in ['price', 'cost', 'rand']):
            return "pricing"
        elif any(word in content_lower for word in ['appointment', 'booking', 'reserve']):
            return "booking_policy"
        elif any(word in content_lower for word in ['return', 'refund', 'policy']):
            return "policies"
        return "general"
    
    def _detect_actions(self, content: str) -> List[str]:
        actions = []
        content_lower = content.lower()
        
        if 'book' in content_lower or 'appointment' in content_lower:
            actions.append("booking")
        if 'order' in content_lower:
            actions.append("ordering")
        if 'email' in content_lower:
            actions.append("email")
        if 'call' in content_lower:
            actions.append("call")
            
        return actions

# Singleton instance
analysis_bot = AnalysisBot()
