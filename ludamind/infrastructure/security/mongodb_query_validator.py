"""
MongoDB Query Security Validator

Validates MongoDB queries to prevent injection and dangerous operations.
"""

import json
import re
import logging
from typing import Any, Dict, List, Optional, Set
from .validation_result import ValidationResult, RiskLevel


logger = logging.getLogger(__name__)


class MongoQuerySecurityValidator:
    """
    Validates MongoDB queries for security threats.

    Implements:
    - JSON validation
    - Blacklist of dangerous operators
    - Whitelist of allowed collections
    - Pipeline depth limits
    - ReDoS (Regular Expression Denial of Service) detection
    """

    # Dangerous MongoDB operators
    DANGEROUS_OPERATORS = {
        '$where',      # Allows arbitrary JavaScript execution
        '$function',   # Allows custom JavaScript functions
        '$accumulator',  # Can execute JavaScript
        '$expr'        # Can be misused (warning only)
    }

    # Eval-like operations (always blocked)
    EVAL_OPERATORS = {
        '$where',
        '$function'
    }

    # Maximum complexity limits
    MAX_PIPELINE_STAGES = 10
    MAX_REGEX_LENGTH = 200
    MAX_ARRAY_SIZE = 1000
    MAX_NESTING_DEPTH = 5

    # ReDoS patterns (catastrophic backtracking)
    REDOS_PATTERNS = [
        r'\([^)]*\)\+',      # (a+)+
        r'\([^)]*\)\*',      # (a*)*
        r'\{[0-9,]+\}\+',    # {n,m}+
        r'\.\*\.\*',         # .*.*
        r'\+\+',             # ++
        r'\*\*',             # **
    ]

    def __init__(self, allowed_collections: Optional[List[str]] = None):
        """
        Initialize validator.

        Args:
            allowed_collections: Whitelist of allowed collection names
        """
        self.allowed_collections = set(allowed_collections or [
            'pharmacies',
            'allpharmacies',
            'bookings',
            'bookingRequests',
            'items',
            'eans',
            'itemPrices',
            'stockItems',
            'stockEvents',
            'users',
            'thirdUsers',
            'payments',
            'invoices',
            'billings',
            'notifications',
            'userNotifications',
            'deliveryEvents',
            'providers',
            'auditEvents',
            'connectionEvents'
        ])

    def validate_query(self, query: Any, collection: Optional[str] = None) -> ValidationResult:
        """
        Validate a MongoDB find query.

        Args:
            query: MongoDB query dict or JSON string
            collection: Collection name (optional)

        Returns:
            ValidationResult
        """
        # Parse if string
        if isinstance(query, str):
            try:
                query = json.loads(query)
            except json.JSONDecodeError as e:
                return ValidationResult.blocked(
                    [f"Invalid JSON: {str(e)}"],
                    RiskLevel.HIGH
                )

        # Validate it's a dict
        if not isinstance(query, dict):
            return ValidationResult.blocked(
                ["Query must be a dictionary"],
                RiskLevel.HIGH
            )

        blocked_reasons = []
        warnings = []

        # Check collection whitelist
        if collection and not self._is_collection_allowed(collection):
            blocked_reasons.append(f"Collection '{collection}' is not in whitelist")

        # Check for dangerous operators
        dangerous_ops = self._check_dangerous_operators(query)
        if dangerous_ops:
            blocked_reasons.append(f"Dangerous operators detected: {', '.join(dangerous_ops)}")

        # Check nesting depth
        depth = self._calculate_nesting_depth(query)
        if depth > self.MAX_NESTING_DEPTH:
            blocked_reasons.append(f"Query nesting too deep: {depth} levels (max {self.MAX_NESTING_DEPTH})")

        # Check for ReDoS in regex
        redos_found = self._check_redos_patterns(query)
        if redos_found:
            blocked_reasons.append(f"Potentially catastrophic regex patterns: {', '.join(redos_found)}")

        # Check array sizes
        large_arrays = self._check_array_sizes(query)
        if large_arrays:
            warnings.append(f"Large arrays in query may impact performance: {large_arrays}")

        # Determine safety
        if blocked_reasons:
            return ValidationResult(
                is_safe=False,
                risk_level=RiskLevel.CRITICAL,
                blocked_reasons=blocked_reasons,
                warnings=warnings
            )
        elif warnings:
            return ValidationResult(
                is_safe=True,
                risk_level=RiskLevel.LOW,
                warnings=warnings
            )
        else:
            return ValidationResult.safe()

    def validate_pipeline(self, pipeline: Any, collection: Optional[str] = None) -> ValidationResult:
        """
        Validate a MongoDB aggregation pipeline.

        Args:
            pipeline: Pipeline array or JSON string
            collection: Collection name (optional)

        Returns:
            ValidationResult
        """
        # Parse if string
        if isinstance(pipeline, str):
            try:
                pipeline = json.loads(pipeline)
            except json.JSONDecodeError as e:
                return ValidationResult.blocked(
                    [f"Invalid JSON: {str(e)}"],
                    RiskLevel.HIGH
                )

        # Validate it's a list
        if not isinstance(pipeline, list):
            return ValidationResult.blocked(
                ["Pipeline must be an array"],
                RiskLevel.HIGH
            )

        blocked_reasons = []
        warnings = []

        # Check collection whitelist
        if collection and not self._is_collection_allowed(collection):
            blocked_reasons.append(f"Collection '{collection}' is not in whitelist")

        # Check pipeline length
        if len(pipeline) > self.MAX_PIPELINE_STAGES:
            blocked_reasons.append(
                f"Pipeline too long: {len(pipeline)} stages (max {self.MAX_PIPELINE_STAGES})"
            )

        # Check each stage
        for i, stage in enumerate(pipeline):
            if not isinstance(stage, dict):
                blocked_reasons.append(f"Stage {i} is not a dictionary")
                continue

            # Check for dangerous operators in stage
            dangerous_ops = self._check_dangerous_operators(stage)
            if dangerous_ops:
                blocked_reasons.append(
                    f"Stage {i} has dangerous operators: {', '.join(dangerous_ops)}"
                )

            # Check nesting depth
            depth = self._calculate_nesting_depth(stage)
            if depth > self.MAX_NESTING_DEPTH:
                warnings.append(f"Stage {i} has deep nesting: {depth} levels")

            # Check for ReDoS
            redos_found = self._check_redos_patterns(stage)
            if redos_found:
                blocked_reasons.append(
                    f"Stage {i} has catastrophic regex: {', '.join(redos_found)}"
                )

        # Lookup operations check
        lookup_count = sum(1 for stage in pipeline if '$lookup' in stage)
        if lookup_count > 3:
            warnings.append(f"Pipeline has {lookup_count} $lookup stages (may be slow)")

        # Determine safety
        if blocked_reasons:
            return ValidationResult(
                is_safe=False,
                risk_level=RiskLevel.CRITICAL,
                blocked_reasons=blocked_reasons,
                warnings=warnings
            )
        elif warnings:
            return ValidationResult(
                is_safe=True,
                risk_level=RiskLevel.MEDIUM,
                warnings=warnings
            )
        else:
            return ValidationResult.safe()

    def _is_collection_allowed(self, collection: str) -> bool:
        """Check if collection is in whitelist."""
        return collection in self.allowed_collections

    def _check_dangerous_operators(self, obj: Any, path: str = "") -> List[str]:
        """
        Recursively check for dangerous operators.

        Args:
            obj: Object to check
            path: Current path (for error reporting)

        Returns:
            List of dangerous operators found
        """
        found = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check if key is a dangerous operator
                if key in self.DANGEROUS_OPERATORS:
                    found.append(f"{path}.{key}" if path else key)

                # Recurse into value
                found.extend(self._check_dangerous_operators(value, f"{path}.{key}" if path else key))

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                found.extend(self._check_dangerous_operators(item, f"{path}[{i}]"))

        return found

    def _calculate_nesting_depth(self, obj: Any, current_depth: int = 0) -> int:
        """
        Calculate maximum nesting depth of an object.

        Args:
            obj: Object to analyze
            current_depth: Current recursion depth

        Returns:
            Maximum depth
        """
        if not isinstance(obj, (dict, list)):
            return current_depth

        max_depth = current_depth

        if isinstance(obj, dict):
            for value in obj.values():
                depth = self._calculate_nesting_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)

        elif isinstance(obj, list):
            for item in obj:
                depth = self._calculate_nesting_depth(item, current_depth + 1)
                max_depth = max(max_depth, depth)

        return max_depth

    def _check_redos_patterns(self, obj: Any) -> List[str]:
        """
        Check for ReDoS (Regular Expression Denial of Service) patterns.

        Args:
            obj: Object to check

        Returns:
            List of problematic regex patterns found
        """
        found = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check $regex operator
                if key == '$regex':
                    if isinstance(value, str):
                        # Check pattern length
                        if len(value) > self.MAX_REGEX_LENGTH:
                            found.append(f"Regex too long: {len(value)} chars")

                        # Check for ReDoS patterns
                        for pattern in self.REDOS_PATTERNS:
                            if re.search(pattern, value):
                                found.append(f"Catastrophic backtracking pattern: {value[:50]}...")
                                break

                # Recurse
                found.extend(self._check_redos_patterns(value))

        elif isinstance(obj, list):
            for item in obj:
                found.extend(self._check_redos_patterns(item))

        return found

    def _check_array_sizes(self, obj: Any, path: str = "") -> List[str]:
        """
        Check for large arrays that may impact performance.

        Args:
            obj: Object to check
            path: Current path

        Returns:
            List of warnings about large arrays
        """
        warnings = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                warnings.extend(self._check_array_sizes(value, new_path))

        elif isinstance(obj, list):
            if len(obj) > self.MAX_ARRAY_SIZE:
                warnings.append(f"{path}: {len(obj)} elements (max {self.MAX_ARRAY_SIZE})")

            for i, item in enumerate(obj):
                warnings.extend(self._check_array_sizes(item, f"{path}[{i}]"))

        return warnings

    def sanitize_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to sanitize a query by removing dangerous operators.

        Args:
            query: Query to sanitize

        Returns:
            Sanitized query

        Note: Use with caution. Validation should be primary defense.
        """
        if not isinstance(query, dict):
            return query

        sanitized = {}

        for key, value in query.items():
            # Skip dangerous operators
            if key in self.EVAL_OPERATORS:
                logger.warning(f"Removed dangerous operator: {key}")
                continue

            # Recursively sanitize nested dicts
            if isinstance(value, dict):
                sanitized[key] = self.sanitize_query(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_query(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized
