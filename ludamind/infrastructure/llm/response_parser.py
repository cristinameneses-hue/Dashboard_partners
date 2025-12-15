"""
LLM Response Parser

Robust parser for LLM responses with multiple fallback strategies.
"""

import json
import re
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, TypeVar, Union
from pydantic import BaseModel, ValidationError


logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class ParseError(Exception):
    """Raised when all parsing attempts fail."""

    def __init__(self, message: str, original_response: str, attempts: Dict[str, str]):
        """
        Initialize parse error.

        Args:
            message: Error message
            original_response: Original LLM response
            attempts: Dictionary of parsing attempts and their errors
        """
        super().__init__(message)
        self.original_response = original_response
        self.attempts = attempts


@dataclass
class ParseResult:
    """Result of parsing attempt."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    method: Optional[str] = None  # Which method succeeded

    @classmethod
    def success_result(cls, data: Any, method: str) -> 'ParseResult':
        """Create a successful parse result."""
        return cls(success=True, data=data, method=method)

    @classmethod
    def error_result(cls, error: str) -> 'ParseResult':
        """Create an error parse result."""
        return cls(success=False, error=error)


class LLMResponseParser:
    """
    Parse LLM responses with multiple fallback strategies.

    Strategies (in order):
    1. Direct JSON parse
    2. Extract JSON from markdown code blocks
    3. Find first { to last }
    4. Regex extraction of known fields
    5. Return original as text

    Can validate against Pydantic models.
    """

    # Common markdown code fence patterns
    JSON_CODE_PATTERNS = [
        r'```json\s*\n(.*?)\n```',  # ```json ... ```
        r'```\s*\n(.*?)\n```',      # ``` ... ```
        r'`([^`]+)`',                # `...`
    ]

    # Patterns for common fields
    FIELD_PATTERNS = {
        'query': [
            r'"query"\s*:\s*"([^"]+)"',
            r"'query'\s*:\s*'([^']+)'",
            r'query:\s*"([^"]+)"',
        ],
        'database': [
            r'"database"\s*:\s*"([^"]+)"',
            r"'database'\s*:\s*'([^']+)'",
            r'database:\s*"([^"]+)"',
        ],
        'explanation': [
            r'"explanation"\s*:\s*"([^"]+)"',
            r"'explanation'\s*:\s*'([^']+)'",
        ],
        'error': [
            r'"error"\s*:\s*"([^"]+)"',
            r"'error'\s*:\s*'([^']+)'",
        ]
    }

    def __init__(self, log_attempts: bool = True):
        """
        Initialize parser.

        Args:
            log_attempts: Whether to log each parsing attempt
        """
        self.log_attempts = log_attempts

    def parse_json(self, response: str, model: Optional[Type[T]] = None) -> Union[Dict[str, Any], T]:
        """
        Parse LLM response as JSON with fallbacks.

        Args:
            response: Raw LLM response string
            model: Optional Pydantic model to validate against

        Returns:
            Parsed JSON data or validated model instance

        Raises:
            ParseError: If all parsing attempts fail
        """
        if not response or not isinstance(response, str):
            raise ParseError(
                "Response is empty or not a string",
                str(response),
                {}
            )

        attempts = {}

        # Strategy 1: Direct JSON parse
        result = self._try_direct_json_parse(response)
        attempts['direct_json'] = result.error or "Success"
        if result.success:
            logger.info(f"Parsed response using method: {result.method}")
            return self._validate_model(result.data, model) if model else result.data

        # Strategy 2: Extract from markdown
        result = self._try_markdown_extraction(response)
        attempts['markdown_extraction'] = result.error or "Success"
        if result.success:
            if self.log_attempts:
                logger.info(f"Parsed response using method: {result.method}")
            return self._validate_model(result.data, model) if model else result.data

        # Strategy 3: Find first { to last }
        result = self._try_bracket_extraction(response)
        attempts['bracket_extraction'] = result.error or "Success"
        if result.success:
            if self.log_attempts:
                logger.info(f"Parsed response using method: {result.method}")
            return self._validate_model(result.data, model) if model else result.data

        # Strategy 4: Regex extraction of fields
        result = self._try_regex_extraction(response)
        attempts['regex_extraction'] = result.error or "Success"
        if result.success:
            if self.log_attempts:
                logger.warning(f"Parsed response using fallback method: {result.method}")
            return self._validate_model(result.data, model) if model else result.data

        # All strategies failed
        logger.error(f"All parsing strategies failed for response: {response[:200]}...")
        raise ParseError(
            "All parsing strategies failed",
            response,
            attempts
        )

    def parse_json_safe(self, response: str, default: Any = None) -> Any:
        """
        Parse JSON with safe fallback (no exceptions).

        Args:
            response: Raw LLM response
            default: Value to return on failure

        Returns:
            Parsed data or default value
        """
        try:
            return self.parse_json(response)
        except ParseError as e:
            logger.warning(f"Parse failed, returning default: {e}")
            return default

    def _try_direct_json_parse(self, response: str) -> ParseResult:
        """Try to parse response directly as JSON."""
        try:
            data = json.loads(response.strip())
            return ParseResult.success_result(data, "direct_json")
        except json.JSONDecodeError as e:
            return ParseResult.error_result(f"JSONDecodeError: {str(e)}")
        except Exception as e:
            return ParseResult.error_result(f"Unexpected error: {str(e)}")

    def _try_markdown_extraction(self, response: str) -> ParseResult:
        """Try to extract JSON from markdown code blocks."""
        for i, pattern in enumerate(self.JSON_CODE_PATTERNS):
            try:
                matches = re.findall(pattern, response, re.DOTALL)
                if matches:
                    # Try each match (usually just one)
                    for match in matches:
                        try:
                            data = json.loads(match.strip())
                            return ParseResult.success_result(
                                data,
                                f"markdown_extraction_pattern_{i}"
                            )
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.debug(f"Markdown pattern {i} failed: {e}")
                continue

        return ParseResult.error_result("No valid JSON found in markdown blocks")

    def _try_bracket_extraction(self, response: str) -> ParseResult:
        """Try to find JSON by looking for first { to last }."""
        try:
            # Find first { and last }
            first_brace = response.find('{')
            last_brace = response.rfind('}')

            if first_brace == -1 or last_brace == -1 or first_brace >= last_brace:
                return ParseResult.error_result("No valid { } pair found")

            json_str = response[first_brace:last_brace + 1]

            # Try to parse
            try:
                data = json.loads(json_str)
                return ParseResult.success_result(data, "bracket_extraction")
            except json.JSONDecodeError as e:
                return ParseResult.error_result(f"Invalid JSON between braces: {str(e)}")

        except Exception as e:
            return ParseResult.error_result(f"Bracket extraction failed: {str(e)}")

    def _try_regex_extraction(self, response: str) -> ParseResult:
        """Try to extract known fields using regex."""
        try:
            extracted = {}

            for field, patterns in self.FIELD_PATTERNS.items():
                for pattern in patterns:
                    match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                    if match:
                        extracted[field] = match.group(1)
                        break

            if extracted:
                return ParseResult.success_result(extracted, "regex_extraction")
            else:
                return ParseResult.error_result("No fields extracted via regex")

        except Exception as e:
            return ParseResult.error_result(f"Regex extraction failed: {str(e)}")

    def _validate_model(self, data: Dict[str, Any], model: Type[T]) -> T:
        """
        Validate data against Pydantic model.

        Args:
            data: Dictionary to validate
            model: Pydantic model class

        Returns:
            Validated model instance

        Raises:
            ParseError: If validation fails
        """
        try:
            return model(**data)
        except ValidationError as e:
            logger.error(f"Model validation failed: {e}")
            raise ParseError(
                f"Validation failed: {str(e)}",
                json.dumps(data),
                {'validation': str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            raise ParseError(
                f"Unexpected validation error: {str(e)}",
                json.dumps(data),
                {'validation': str(e)}
            )

    def extract_text_fallback(self, response: str) -> str:
        """
        Extract clean text from response (ultimate fallback).

        Args:
            response: Raw response

        Returns:
            Cleaned text
        """
        # Remove markdown code blocks
        text = re.sub(r'```[a-z]*\n.*?\n```', '', response, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r'`[^`]+`', '', text)

        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text


# Convenience function
def parse_llm_json(response: str, model: Optional[Type[T]] = None, safe: bool = False) -> Union[Dict, T, None]:
    """
    Parse LLM JSON response (convenience function).

    Args:
        response: LLM response string
        model: Optional Pydantic model
        safe: If True, return None on error instead of raising

    Returns:
        Parsed data, model instance, or None

    Raises:
        ParseError: If parsing fails (only when safe=False)
    """
    parser = LLMResponseParser(log_attempts=not safe)

    if safe:
        return parser.parse_json_safe(response, default=None)
    else:
        return parser.parse_json(response, model=model)
