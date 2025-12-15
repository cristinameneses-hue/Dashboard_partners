"""
SQL Query Security Validator

Validates SQL queries to prevent injection attacks and dangerous operations.
"""

import re
import logging
from typing import List, Set, Optional
from .validation_result import ValidationResult, RiskLevel


logger = logging.getLogger(__name__)


class QuerySecurityValidator:
    """
    Validates SQL queries for security threats.

    Implements:
    - Blacklist of dangerous SQL operations
    - Whitelist of allowed tables
    - Query complexity limits
    - SQL injection pattern detection
    """

    # Dangerous SQL keywords that should always be blocked
    DANGEROUS_KEYWORDS = {
        'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE',
        'EXEC', 'EXECUTE', 'SHUTDOWN', 'KILL', 'USE',
        'LOAD_FILE', 'INTO OUTFILE', 'INTO DUMPFILE',
        'BENCHMARK', 'SLEEP'
    }

    # Dangerous functions that can be used for attacks
    DANGEROUS_FUNCTIONS = {
        'LOAD_FILE', 'OUTFILE', 'DUMPFILE', 'BENCHMARK',
        'EXTRACTVALUE', 'UPDATEXML', 'XMLTYPE', 'DBMS_XMLGEN'
    }

    # SQL comment patterns (used in injection)
    COMMENT_PATTERNS = [
        r'--',           # SQL line comment
        r'/\*.*?\*/',    # SQL block comment
        r'#',            # MySQL comment
        r';.*--',        # Statement terminator with comment
    ]

    # Maximum allowed values
    MAX_ROWS = 1000
    MAX_JOINS = 4
    MAX_QUERY_LENGTH = 5000

    def __init__(self, allowed_tables: Optional[List[str]] = None):
        """
        Initialize validator.

        Args:
            allowed_tables: Whitelist of allowed table names (patterns supported)
        """
        self.allowed_tables = set(allowed_tables or [
            'trends.*',
            'bookings.*',
            'farmacias.*',
            'productos.*',
            'pharmacies.*',
            'items.*',
            'stockItems.*',
            'users.*'
        ])

    def validate(self, query: str) -> ValidationResult:
        """
        Validate a SQL query for security issues.

        Args:
            query: SQL query to validate

        Returns:
            ValidationResult with safety status and details
        """
        if not query or not isinstance(query, str):
            return ValidationResult.blocked(
                ["Query is empty or not a string"],
                RiskLevel.HIGH
            )

        # Normalize query for analysis
        query_clean = self._remove_strings(query)  # Remove strings first to avoid false positives
        query_upper = query.upper()
        query_clean_upper = query_clean.upper()

        blocked_reasons = []
        warnings = []

        # Check 1: Query length
        if len(query) > self.MAX_QUERY_LENGTH:
            blocked_reasons.append(f"Query exceeds maximum length ({self.MAX_QUERY_LENGTH} chars)")

        # Check 2: Dangerous keywords (use query_clean_upper to avoid false positives from strings)
        dangerous_found = self._check_dangerous_keywords(query_clean_upper)
        if dangerous_found:
            blocked_reasons.append(f"Dangerous SQL operations detected: {', '.join(dangerous_found)}")

        # Check 3: Dangerous functions (use query_clean_upper)
        dangerous_funcs = self._check_dangerous_functions(query_clean_upper)
        if dangerous_funcs:
            blocked_reasons.append(f"Dangerous SQL functions detected: {', '.join(dangerous_funcs)}")

        # Check 4: SQL comments (possible injection)
        if self._check_sql_comments(query):
            blocked_reasons.append("SQL comments detected (potential injection attempt)")

        # Check 5: DELETE/UPDATE without WHERE
        if self._check_unsafe_modifications(query_upper):
            blocked_reasons.append("DELETE or UPDATE without WHERE clause detected")

        # Check 6: UNION injection patterns
        if self._check_union_injection(query_clean):
            blocked_reasons.append("Suspicious UNION statement detected")

        # Check 7: Multiple statements (statement stacking)
        if self._check_statement_stacking(query_clean):
            blocked_reasons.append("Multiple SQL statements detected (statement stacking)")

        # Check 8: Table whitelist
        table_violations = self._check_table_whitelist(query)
        if table_violations:
            warnings.append(f"Queries to non-whitelisted tables: {', '.join(table_violations)}")

        # Check 9: Query complexity
        complexity_issues = self._check_query_complexity(query_upper)
        if complexity_issues:
            warnings.extend(complexity_issues)

        # Check 10: Row limit
        if 'SELECT' in query_upper and 'LIMIT' not in query_upper:
            warnings.append(f"SELECT without LIMIT may return many rows (max {self.MAX_ROWS} enforced)")

        # Determine risk level
        if blocked_reasons:
            risk_level = RiskLevel.CRITICAL
            is_safe = False
        elif warnings:
            risk_level = RiskLevel.MEDIUM
            is_safe = True
        else:
            risk_level = RiskLevel.SAFE
            is_safe = True

        result = ValidationResult(
            is_safe=is_safe,
            risk_level=risk_level,
            blocked_reasons=blocked_reasons,
            warnings=warnings
        )

        # Log validation results
        if not is_safe:
            logger.warning(f"Query blocked: {blocked_reasons[:100]}")
        elif warnings:
            logger.info(f"Query warnings: {warnings[:100]}")

        return result

    def _remove_strings(self, query: str) -> str:
        """Remove string literals from query to avoid false positives."""
        # Remove single-quoted strings
        query = re.sub(r"'[^']*'", "''", query)
        # Remove double-quoted strings
        query = re.sub(r'"[^"]*"', '""', query)
        return query

    def _check_dangerous_keywords(self, query_upper: str) -> List[str]:
        """Check for dangerous SQL keywords."""
        found = []
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_upper):
                found.append(keyword)
        return found

    def _check_dangerous_functions(self, query_upper: str) -> List[str]:
        """Check for dangerous SQL functions."""
        found = []
        for func in self.DANGEROUS_FUNCTIONS:
            if func in query_upper:
                found.append(func)
        return found

    def _check_sql_comments(self, query: str) -> bool:
        """Check for SQL comment patterns."""
        for pattern in self.COMMENT_PATTERNS:
            if re.search(pattern, query):
                return True
        return False

    def _check_unsafe_modifications(self, query_upper: str) -> bool:
        """Check for DELETE/UPDATE without WHERE clause."""
        # DELETE without WHERE - check if WHERE appears after DELETE
        if 'DELETE' in query_upper and 'FROM' in query_upper:
            # Simple check: if DELETE...FROM exists but no WHERE follows
            delete_pattern = r'\bDELETE\s+FROM\s+\w+'
            if re.search(delete_pattern, query_upper):
                # Check if WHERE appears after DELETE
                delete_match = re.search(delete_pattern, query_upper)
                if delete_match:
                    text_after_delete = query_upper[delete_match.end():]
                    if 'WHERE' not in text_after_delete:
                        return True

        # UPDATE without WHERE - check if WHERE appears after SET
        if 'UPDATE' in query_upper and 'SET' in query_upper:
            update_pattern = r'\bUPDATE\s+\w+\s+SET\s+'
            if re.search(update_pattern, query_upper):
                update_match = re.search(update_pattern, query_upper)
                if update_match:
                    text_after_set = query_upper[update_match.end():]
                    if 'WHERE' not in text_after_set:
                        return True

        return False

    def _check_union_injection(self, query_clean: str) -> bool:
        """Check for UNION-based injection patterns."""
        query_upper = query_clean.upper()

        # Multiple UNIONs or UNION with suspicious patterns
        union_count = query_upper.count('UNION')
        if union_count > 2:
            return True

        # UNION with SELECT NULL (common in injection)
        if 'UNION' in query_upper and 'NULL' in query_upper:
            if re.search(r'UNION.*SELECT.*NULL', query_upper):
                return True

        return False

    def _check_statement_stacking(self, query_clean: str) -> bool:
        """Check for multiple SQL statements (separated by semicolons)."""
        # Count semicolons (excluding those in strings, already removed)
        semicolons = query_clean.count(';')

        # Allow one semicolon at end
        if semicolons > 1:
            return True

        if semicolons == 1 and not query_clean.strip().endswith(';'):
            return True

        return False

    def _check_table_whitelist(self, query: str) -> List[str]:
        """Check if query accesses only whitelisted tables."""
        # Extract table names from FROM and JOIN clauses
        from_pattern = r'\bFROM\s+([a-zA-Z0-9_\.]+)'
        join_pattern = r'\bJOIN\s+([a-zA-Z0-9_\.]+)'

        tables = set()
        tables.update(re.findall(from_pattern, query, re.IGNORECASE))
        tables.update(re.findall(join_pattern, query, re.IGNORECASE))

        violations = []
        for table in tables:
            if not self._is_table_allowed(table):
                violations.append(table)

        return violations

    def _is_table_allowed(self, table: str) -> bool:
        """Check if table is in whitelist."""
        for allowed in self.allowed_tables:
            if allowed.endswith('.*'):
                # Prefix match
                prefix = allowed[:-2]
                if table.startswith(prefix):
                    return True
            elif allowed == table:
                return True
        return False

    def _check_query_complexity(self, query_upper: str) -> List[str]:
        """Check query complexity limits."""
        issues = []

        # Count JOINs
        join_count = query_upper.count('JOIN')
        if join_count > self.MAX_JOINS:
            issues.append(f"Query has {join_count} JOINs (max {self.MAX_JOINS})")

        # Nested subqueries
        nested_level = query_upper.count('SELECT')
        if nested_level > 3:
            issues.append(f"Query has {nested_level} nested SELECT statements (limit 3)")

        return issues

    def enforce_row_limit(self, query: str) -> str:
        """
        Enforce row limit on SELECT queries.

        Args:
            query: SQL query

        Returns:
            Query with LIMIT enforced
        """
        query_upper = query.upper()

        if 'SELECT' not in query_upper:
            return query

        if 'LIMIT' in query_upper:
            # Check if limit exceeds max
            limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
            if limit_match:
                limit_value = int(limit_match.group(1))
                if limit_value > self.MAX_ROWS:
                    # Replace with max limit
                    query = re.sub(
                        r'LIMIT\s+\d+',
                        f'LIMIT {self.MAX_ROWS}',
                        query,
                        flags=re.IGNORECASE
                    )
        else:
            # Add LIMIT
            query = query.rstrip(';').strip() + f' LIMIT {self.MAX_ROWS}'

        return query
