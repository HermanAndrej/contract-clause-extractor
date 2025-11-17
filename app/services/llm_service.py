import asyncio
import json
import re
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from app.config import settings


class LLMService:
    """Service for extracting clauses using LLM APIs."""

    COMMON_CLAUSE_TYPES = [
        "termination",
        "payment",
        "confidentiality",
        "liability",
        "indemnification",
        "governing_law",
        "dispute_resolution",
        "intellectual_property",
        "warranty",
        "force_majeure",
        "assignment",
        "severability",
        "entire_agreement",
        "amendment",
        "notices",
    ]

    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self._client = client
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

    def _ensure_client(self) -> AsyncOpenAI:
        """Create an OpenAI client if one was not injected."""
        if self._client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    # ----------------------------------------------------
    # Prompt builder
    # ----------------------------------------------------
    def _build_extraction_prompt(self, text: str, is_chunk: bool = False) -> str:
        chunk_note = (
            "\nNote: This is a chunk of a larger document. Extract only from this portion."
            if is_chunk else ""
        )

        return f"""
You are a legal document analysis expert. Extract all legal clauses from the following contract text.
{chunk_note}

Your job:

1. Identify each legal clause
2. Extract the full clause text exactly
3. Assign a clause type (if identifiable)
4. Capture page numbers if present
5. Capture approximate start/end positions (optional best-effort)
6. Return ONLY a JSON array of objects

Common clause types:
{", ".join(self.COMMON_CLAUSE_TYPES)}

Each clause object must contain:
- clause_id (string)
- title (string or empty)
- content (string)
- clause_type (string)
- page_number (number or null)
- start_position (number or null)
- end_position (number or null)

Example output:
[
  {{
    "clause_id": "clause_001",
    "title": "Termination",
    "content": "Either party may terminate...",
    "clause_type": "termination",
    "page_number": 2,
    "start_position": 230,
    "end_position": 410
  }}
]

Contract text:
{text}

Return ONLY the JSON array now.
"""

    # ----------------------------------------------------
    # Core extraction logic
    # ----------------------------------------------------
    async def extract_clauses(self, text: str, is_chunk: bool = False) -> List[Dict]:
        prompt = self._build_extraction_prompt(text, is_chunk)

        try:
            from openai import BadRequestError
            client = self._ensure_client()
            
            # Build base parameters
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Return only valid JSON arrays."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": self.temperature,
            }
            
            # Try max_completion_tokens first (required for gpt-5-mini and newer models)
            try:
                api_params["max_completion_tokens"] = self.max_tokens
                response = await client.chat.completions.create(**api_params)
            except TypeError:
                # SDK doesn't recognize max_completion_tokens, try passing directly
                try:
                    del api_params["max_completion_tokens"]
                    response = await client.chat.completions.create(
                        **api_params,
                        max_completion_tokens=self.max_tokens
                    )
                except Exception:
                    # Fallback to max_tokens for older models
                    response = await client.chat.completions.create(
                        **api_params,
                        max_tokens=self.max_tokens
                    )
            except BadRequestError as e:
                # API-level error - check what it says
                error_str = str(e).lower()
                if "use 'max_completion_tokens'" in error_str:
                    del api_params["max_completion_tokens"]
                    response = await client.chat.completions.create(
                        **api_params,
                        max_completion_tokens=self.max_tokens
                    )
                else:
                    raise

            raw = response.choices[0].message.content.strip()

            # Clean Markdown wrappers
            if raw.startswith("```"):
                raw = raw.strip("`").replace("json", "").strip()

            # Try parse directly
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                # Try to extract valid JSON array
                match = re.search(r"\[.*\]", raw, re.DOTALL)
                if not match:
                    return []
                try:
                    parsed = json.loads(match.group())
                except json.JSONDecodeError:
                    return []

            # Validate parsed data
            if not isinstance(parsed, list):
                if isinstance(parsed, dict) and "clauses" in parsed:
                    parsed = parsed["clauses"]
                else:
                    return []

            # Normalize output
            clauses = []
            for i, c in enumerate(parsed):
                if not isinstance(c, dict) or "content" not in c:
                    continue

                clauses.append({
                    "clause_id": c.get("clause_id", f"clause_{i+1:03d}"),
                    "title": c.get("title", "") or "",
                    "content": c.get("content", "") or "",
                    "clause_type": c.get("clause_type", "other"),
                    "page_number": c.get("page_number"),
                    "start_position": c.get("start_position"),
                    "end_position": c.get("end_position"),
                })

            return clauses

        except Exception as e:
            # Log error but don't print full traceback in production
            print(f"Error in extract_clauses: {e}")
            return []

    # ----------------------------------------------------
    # Multi-chunk extraction
    # ----------------------------------------------------
    async def extract_clauses_from_chunks(self, chunks: List[str]) -> List[Dict]:
        all_clauses = []

        for idx, chunk in enumerate(chunks):
            try:
                results = await self.extract_clauses(chunk, is_chunk=True)

                # Ensure global unique clause IDs
                for r in results:
                    r["clause_id"] = f"clause_{len(all_clauses) + 1:03d}"

                all_clauses.extend(results)

                # Add small delay to avoid rate limiting
                if idx < len(chunks) - 1:
                    await asyncio.sleep(0.4)

            except Exception as e:
                print(f"Error processing chunk {idx+1}: {e}")
                continue

        return all_clauses
