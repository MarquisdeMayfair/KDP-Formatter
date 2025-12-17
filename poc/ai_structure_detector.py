"""
AI-Powered Structure Detection for KDP Formatter

This module uses OpenAI's GPT models to intelligently detect document structure
from plain text, including chapters, headings, paragraphs, quotes, footnotes,
and front/back matter.

Features:
- Text chunking for handling large documents
- JSON mode for deterministic, structured output
- Cost tracking and logging
- Fallback to regex detection on API failure
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None

try:
    import tiktoken
except ImportError:
    tiktoken = None

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    # Fallback retry decorator if tenacity not available
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def stop_after_attempt(n): return None
    def wait_exponential(**kwargs): return None
    def retry_if_exception_type(exc): return None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CostTracker:
    """Tracks API usage costs and metadata"""
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    api_calls: int = 0
    model_used: str = ""
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def add_call(self, tokens_used: int, prompt_tokens: int, completion_tokens: int,
                 cost: float, model: str, chunk_info: Optional[Dict] = None):
        """Record a single API call"""
        self.api_calls += 1
        self.total_tokens += tokens_used
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_cost += cost
        self.model_used = model

        call_info = {
            "call_number": self.api_calls,
            "model": model,
            "tokens_used": tokens_used,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost,
            "chunk_info": chunk_info or {}
        }
        self.calls.append(call_info)

        logger.info(f"API Call {self.api_calls}: {tokens_used} tokens, ${cost:.6f} ({model})")

    def get_summary(self) -> Dict[str, Any]:
        """Get cost and usage summary"""
        return {
            "total_api_calls": self.api_calls,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_cost": round(self.total_cost, 6),
            "model_used": self.model_used,
            "calls": self.calls
        }

    def reset(self):
        """Reset all counters"""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost = 0.0
        self.api_calls = 0
        self.calls.clear()


class AIStructureDetector:
    """AI-powered document structure detection using OpenAI"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        """
        Initialize AI detector

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (gpt-4-turbo-preview or gpt-3.5-turbo)
        """
        if openai is None:
            raise ImportError("openai package is required for AI detection")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.cost_tracker = CostTracker()

        # Pricing per 1k tokens (as of 2024)
        self.pricing = {
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }

        # Note: Keep self.model as given, fallback pricing will be used in cost calculations

    def chunk_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """
        Split text into manageable chunks for API calls

        Args:
            text: Full document text
            chunk_size: Target chunk size in characters (approximates token count)

        Returns:
            List of text chunks
        """
        if not text:
            return []

        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        logger.info(f"Split text into {len(chunks)} chunks (avg {len(text)/len(chunks):.0f} chars each)")
        return chunks

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(openai.APIError) if (retry_if_exception_type and openai) else None
    )
    def _call_openai_api(self, prompt: str, chunk_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make API call to OpenAI with retry logic

        Args:
            prompt: Formatted prompt for structure detection
            chunk_info: Metadata about the chunk being processed

        Returns:
            Parsed JSON response from OpenAI
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a conservative book-structure tagger. Output strict JSON only, matching the provided schema."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # Deterministic output
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            # Track costs
            usage = response.usage
            if usage:
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
                total_tokens = usage.total_tokens

                # Calculate cost using fallback pricing if model not defined
                pricing = self.pricing.get(self.model, self.pricing["gpt-4-turbo-preview"])
                if self.model not in self.pricing:
                    logger.warning(f"Using fallback pricing for unknown model {self.model}")

                input_cost = (prompt_tokens / 1000) * pricing["input"]
                output_cost = (completion_tokens / 1000) * pricing["output"]
                total_cost = input_cost + output_cost

                self.cost_tracker.add_call(
                    tokens_used=total_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost=total_cost,
                    model=self.model,
                    chunk_info=chunk_info
                )

            return result

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            raise ValueError(f"Invalid JSON response from OpenAI: {content[:200]}...")

    def detect_structure_chunk(self, text_chunk: str, chunk_number: int = 1,
                             total_chunks: int = 1) -> Dict[str, Any]:
        """
        Detect structure in a single text chunk

        Args:
            text_chunk: Text chunk to analyze
            chunk_number: Current chunk number (for logging)
            total_chunks: Total number of chunks (for context)

        Returns:
            Structured data dictionary
        """
        prompt = f"""Given this raw text chunk ({chunk_number}/{total_chunks}), detect chapters, headings (H1-H3), paragraphs, quotes, code blocks, images (with nearby captions), footnotes, and front/back matter.

Do not typeset; do not invent content; do not reword. Return JSON with exact original text (preserve italics/ALL CAPS markers), plus {{full_bleed:true|false}} hints if a line says 'FULL PAGE IMAGE' etc.

JSON Schema:
{{
  "blocks": [
    {{
      "type": "chapter|heading|paragraph|quote|footnote|front_matter|back_matter|image",
      "level": 1-3,  // for headings only
      "text": "exact original text",
      "style": "normal|blockquote|italic|bold|code",
      "metadata": {{
        "full_bleed": false,
        "attribution": "",  // for quotes
        "caption": "",      // for images
        "reference": ""     // for footnotes
      }}
    }}
  ],
  "chunk_info": {{
    "chunk_number": {chunk_number},
    "total_chunks": {total_chunks},
    "word_count": {len(text_chunk.split())}
  }}
}}

Text to analyze:
{text_chunk}
"""

        chunk_info = {
            "chunk_number": chunk_number,
            "total_chunks": total_chunks,
            "word_count": len(text_chunk.split())
        }

        try:
            result = self._call_openai_api(prompt, chunk_info)
            logger.info(f"Successfully processed chunk {chunk_number}/{total_chunks}")
            return result
        except Exception as e:
            logger.error(f"Failed to process chunk {chunk_number}/{total_chunks}: {e}")
            # Return minimal fallback structure
            return {
                "blocks": [{
                    "type": "paragraph",
                    "text": text_chunk,
                    "style": "normal",
                    "metadata": {}
                }],
                "chunk_info": chunk_info
            }

    def detect_document_structure(self, text: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Detect complete document structure using AI

        Args:
            text: Full document text
            metadata: Optional document metadata

        Returns:
            Dictionary containing:
            - structured_blocks: List of detected structural elements
            - cost_summary: API usage and cost information
            - detection_metadata: Processing information
        """
        logger.info(f"Starting AI structure detection for document ({len(text)} chars, {len(text.split())} words)")

        # Chunk the text
        chunks = self.chunk_text(text)
        if not chunks:
            logger.warning("No text chunks to process")
            return {
                "structured_blocks": [],
                "cost_summary": self.cost_tracker.get_summary(),
                "detection_metadata": {"error": "No text to process"}
            }

        # Process each chunk
        all_blocks = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{len(chunks)}")
            chunk_result = self.detect_structure_chunk(chunk, i, len(chunks))

            # Extract blocks from chunk result
            chunk_blocks = chunk_result.get("blocks", [])
            all_blocks.extend(chunk_blocks)

        # Aggregate results
        result = {
            "structured_blocks": all_blocks,
            "cost_summary": self.cost_tracker.get_summary(),
            "detection_metadata": {
                "total_chunks": len(chunks),
                "total_blocks": len(all_blocks),
                "model_used": self.model,
                "detection_method": "ai",
                "processing_timestamp": None  # Could add timestamp here
            }
        }

        total_cost = result["cost_summary"]["total_cost"]
        logger.info(f"AI detection complete: {len(all_blocks)} blocks detected, ${total_cost:.4f} total cost")

        return result


# Convenience function for external use
def detect_document_structure(text: str, metadata: Optional[Dict] = None,
                            api_key: Optional[str] = None,
                            model: str = "gpt-4-turbo-preview") -> Dict[str, Any]:
    """
    Detect document structure using AI

    Args:
        text: Full document text
        metadata: Optional document metadata
        api_key: OpenAI API key (defaults to env var)
        model: OpenAI model to use

    Returns:
        Structured document data with cost information
    """
    detector = AIStructureDetector(api_key=api_key, model=model)
    return detector.detect_document_structure(text, metadata)
