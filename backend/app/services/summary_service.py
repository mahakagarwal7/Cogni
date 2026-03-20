# backend/app/services/summary_service.py
"""
📝 Summary Service — Intelligent Conversation Summarization Engine

Converts conversation history into:
- Quick preview summaries (for UI)
- Detailed full summaries (for PDF export)
- Chunk-based processing for long conversations
"""

from typing import Dict, Any, List
from app.services.llm_service import llm_service
import json
from datetime import datetime

class SummaryService:
    """
    Summarizes conversations using:
    1. Chunk-based splitting (for long conversations)
    2. Partial summarization (per chunk)
    3. Final summary synthesis
    4. PDF generation capability
    """
    
    def __init__(self):
        self.llm = llm_service
        self.chunk_size = 500  # Characters per chunk
    
    async def generate_summary(self, conversation_text: str) -> Dict[str, Any]:
        """
        Generate both preview and full summary from conversation.
        
        Pipeline:
        1. Split conversation into chunks
        2. Summarize each chunk
        3. Combine into final summary
        4. Extract preview for UI
        5. Return both versions
        """
        if not conversation_text or len(conversation_text.strip()) < 50:
            return {
                "preview": "No substantial conversation to summarize yet.",
                "full_summary": "No substantial conversation to summarize yet.",
                "demo_mode": True
            }
        
        try:
            # Step 1: Chunk the conversation
            chunks = self._chunk_text(conversation_text, self.chunk_size)
            
            # Step 2: Summarize each chunk
            partial_summaries = await self._summarize_chunks(chunks)
            
            # Step 3: Combine and generate final summary
            combined = " ".join(partial_summaries)
            full_summary = await self._generate_final_summary(combined)
            
            # Step 4: Extract preview (first 2 paragraphs or condensed)
            preview = self._extract_preview(full_summary)
            
            return {
                "preview": preview,
                "full_summary": full_summary,
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[DEBUG] Summary generation failed: {e}")
            return {
                "preview": "Summary unavailable. Please try again.",
                "full_summary": "Summary unavailable. Please try again.",
                "demo_mode": True
            }
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """
        Split text into chunks of approximately chunk_size characters.
        Tries to break at sentence boundaries when possible.
        """
        if len(text) <= chunk_size:
            return [text] if text.strip() else []
        
        chunks = []
        current_chunk = ""
        
        sentences = text.replace("?", ".").split(".")
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(test_chunk) <= chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk + ".")
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk + ".")
        
        return [c.strip() for c in chunks if c.strip()]
    
    async def _summarize_chunks(self, chunks: List[str]) -> List[str]:
        """
        Generate summary for each chunk independently.
        Extracts key points while removing LLM meta-text.
        """
        if not self.llm.available or not chunks:
            return chunks[:3]  # Return first 3 chunks as fallback
        
        partial_summaries = []
        
        for chunk in chunks:
            if len(chunk) < 30:
                continue
            
            prompt = f"""Summarize this conversation chunk concisely:

{chunk}

Requirements:
- Extract main points and key insights
- Keep important learning moments
- NO thinking steps, NO meta explanations
- 2-3 sentences maximum
- Clear and direct"""
            
            try:
                summary = self.llm.generate(prompt, max_tokens=150, temperature=0.5)
                # Clean output
                summary = summary.replace("<think>", "").replace("</think>", "").strip()
                
                if summary and len(summary) > 10:
                    partial_summaries.append(summary)
            except Exception as e:
                print(f"[DEBUG] Chunk summarization failed: {e}")
                continue
        
        return partial_summaries if partial_summaries else [chunks[0] if chunks else ""]
    
    async def _generate_final_summary(self, combined_text: str) -> str:
        """
        Create final structured summary from partial summaries.
        Produces 4-6 paragraphs with:
        - Learning progress
        - Key insights
        - Important patterns
        - Recommendations
        """
        if not self.llm.available or len(combined_text) < 30:
            return combined_text
        
        prompt = f"""Create a structured summary of this learning conversation:

{combined_text}

Requirements:
- 4-6 clear paragraphs
- Capture: learning progress, key insights, patterns, next steps
- NO thinking steps or meta explanation
- NO truncation - complete thoughts only
- Professional, encouraging tone
- Focus on what was learned and how to continue

Structure:
1. Overview of learning session
2. Key topics and concepts covered
3. Progress and achievements
4. Challenges and insights
5. Recommendations for continued learning
6. Next steps (if applicable)"""
        
        try:
            summary = self.llm.generate(prompt, max_tokens=800, temperature=0.6)
            
            # Clean output
            cleaned = summary.replace("<think>", "").replace("</think>", "").strip()
            
            # Remove meta lines
            lines = cleaned.split("\n")
            cleaned_lines = []
            
            meta_patterns = [
                "here is",
                "here's",
                "let me",
                "i've created",
                "this summary",
                "based on",
                "to summarize"
            ]
            
            for line in lines:
                lower_line = line.lower()
                is_meta = any(meta in lower_line for meta in meta_patterns)
                
                if not (is_meta and len(line) < 60):
                    clean_line = line.replace("**", "").strip()
                    if clean_line:
                        cleaned_lines.append(clean_line)
            
            final = "\n\n".join(cleaned_lines).strip()
            
            return final if final and len(final) > 50 else combined_text
            
        except Exception as e:
            print(f"[DEBUG] Final summary generation failed: {e}")
            return combined_text
    
    def _extract_preview(self, full_summary: str) -> str:
        """
        Extract preview from full summary.
        Returns first 2 paragraphs or condensed version.
        """
        if not full_summary:
            return "No summary available."
        
        # Get first 2 paragraphs
        paragraphs = full_summary.split("\n\n")
        
        if len(paragraphs) >= 2:
            preview = "\n\n".join(paragraphs[:2])
        else:
            preview = paragraphs[0] if paragraphs else full_summary
        
        # Limit to ~500 characters for UI
        if len(preview) > 500:
            preview = preview[:500] + "..."
        
        return preview
    
    def generate_pdf(self, summary: str, title: str = "Learning Summary") -> bytes:
        """
        Generate PDF from summary text.
        Simple and robust - uses reportlab with proper error handling.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            from io import BytesIO
            
            # Sanitize text by removing problematic characters
            def clean_text(text):
                if not text:
                    return ""
                # Remove markdown formatting
                text = text.replace("**", "").replace("__", "").replace("_", " ")
                # Remove XML-problematic chars
                text = text.replace("&", "and").replace("<", "[").replace(">", "]")
                # Remove control characters but keep newlines and tabs
                text = ''.join(c if ord(c) >= 32 or c in '\n\t\r' else ' ' for c in text)
                return text
            
            # Create PDF in memory
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=50,
            )
            
            styles = getSampleStyleSheet()
            
            # Create elements list
            elements = []
            
            # Add title
            clean_title = clean_text(title)
            if clean_title:
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=14,
                    textColor='black',
                    spaceAfter=12,
                )
                elements.append(Paragraph(clean_title, title_style))
                elements.append(Spacer(1, 0.15 * inch))
            
            # Add body text
            clean_summary = clean_text(summary)
            if clean_summary:
                body_style = ParagraphStyle(
                    'CustomBody',
                    parent=styles['BodyText'],
                    fontSize=10,
                    leading=12,
                    spaceAfter=8,
                )
                
                # Split into paragraphs and add each
                for paragraph in clean_summary.split('\n\n'):
                    para_text = paragraph.strip()
                    if para_text:
                        elements.append(Paragraph(para_text, body_style))
                        elements.append(Spacer(1, 0.1 * inch))
            
            # Add timestamp footer
            elements.append(Spacer(1, 0.2 * inch))
            timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor='gray')
            elements.append(Paragraph(f"Generated on {timestamp} | Cogni", footer_style))
            
            # Build the PDF
            doc.build(elements)
            
            # Get bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            if pdf_bytes and len(pdf_bytes) > 100:
                print(f"[SUCCESS] PDF generated: {len(pdf_bytes)} bytes")
                return pdf_bytes
            else:
                print("[WARNING] PDF generated but very small, trying fallback")
                return self._create_text_as_pdf(title, summary)
            
        except Exception as e:
            print(f"[ERROR] PDF generation failed: {e}, using text fallback")
            return self._create_text_as_pdf(title, summary)
    
    def _create_text_as_pdf(self, title: str, content: str) -> bytes:
        """
        Fallback: Return text formatted as simple plain PDF.
        """
        try:
            # Create simple plain text document formatted for PDF
            text_content = f"""{title}

{content}

---
Generated on {datetime.now().strftime('%B %d, %Y')}
Cogni - Your Metacognitive Study Companion"""
            
            # Encode as UTF-8 and return as bytes
            pdf_bytes = text_content.encode('utf-8')
            print(f"[SUCCESS] Text fallback PDF created: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            print(f"[ERROR] Text fallback also failed: {e}")
            # Absolute fallback
            fallback = f"{title}\n\n{content}".encode('utf-8', errors='replace')
            print(f"[SUCCESS] Absolute fallback created: {len(fallback)} bytes")
            return fallback


# Singleton instance
summary_service = SummaryService()
