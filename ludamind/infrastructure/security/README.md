# 🔒 Security Module - Query Validators

## Overview

This module provides comprehensive security validation for SQL and MongoDB queries to prevent injection attacks, dangerous operations, and performance issues.

---

## 📦 Components

### 1. **QuerySecurityValidator** (SQL)

Validates SQL queries to prevent:
- SQL Injection attacks
- Dangerous operations (DROP, TRUNCATE, ALTER, etc.)
- Excessive query complexity
- Unauthorized table access

### 2. **MongoQuerySecurityValidator** (MongoDB)

Validates MongoDB queries to prevent:
- JavaScript injection ($where, $function)
- ReDoS (Regular Expression Denial of Service)
- Excessive pipeline complexity
- Unauthorized collection access

### 3. **LLMResponseParser** (Response Parsing)

Robustly parses LLM responses with multiple fallback strategies.

---

## 🚀 Quick Start

### SQL Validation

```python
from infrastructure.security import QuerySecurityValidator

# Create validator
validator = QuerySecurityValidator(
    allowed_tables=['trends.*', 'pharmacies', 'bookings']
)

# Validate query
result = validator.validate(
    "SELECT * FROM pharmacies WHERE active = 1 LIMIT 10"
)

if result.is_safe:
    print("Query is safe to execute")
    # Execute query
else:
    print(f"Query blocked: {result.blocked_reasons}")
    # Reject query
```

### MongoDB Validation

```python
from infrastructure.security import MongoQuerySecurityValidator

# Create validator
validator = MongoQuerySecurityValidator(
    allowed_collections=['pharmacies', 'bookings', 'items']
)

# Validate find query
query = {"active": 1, "city": "Madrid"}
result = validator.validate_query(query, collection="pharmacies")

if result.is_safe:
    # Execute query
    db.pharmacies.find(query)
else:
    print(f"Query blocked: {result.blocked_reasons}")

# Validate aggregation pipeline
pipeline = [
    {"$match": {"active": 1}},
    {"$group": {"_id": "$city", "count": {"$sum": 1}}}
]
result = validator.validate_pipeline(pipeline, collection="pharmacies")
```

### LLM Response Parsing

```python
from infrastructure.llm import LLMResponseParser, parse_llm_json
from pydantic import BaseModel

# Define expected structure
class QueryResponse(BaseModel):
    query: str
    database: str
    explanation: str

# Parse LLM response
response = '''
Here's the query:
```json
{
    "query": "SELECT * FROM users LIMIT 10",
    "database": "mysql",
    "explanation": "Fetches first 10 users"
}
```
'''

# Option 1: With error handling
try:
    result = parse_llm_json(response, model=QueryResponse)
    print(result.query)  # Type-safe access
except ParseError as e:
    print(f"Parse failed: {e}")

# Option 2: Safe mode (no exceptions)
result = parse_llm_json(response, safe=True)
if result:
    print(result)
else:
    print("Could not parse response")
```

---

## 📋 Security Features

### SQL Validator

#### ✅ Safe Operations
- SELECT with WHERE, LIMIT
- JOINs (up to 4 tables)
- Aggregations (GROUP BY, ORDER BY)
- Subqueries (up to 3 levels)

#### ❌ Blocked Operations
- **DDL:** DROP, TRUNCATE, ALTER, CREATE
- **Permissions:** GRANT, REVOKE
- **File Access:** LOAD_FILE, INTO OUTFILE
- **System:** EXEC, SHUTDOWN, KILL
- **Injection:** SQL comments (--,  /**/, #)
- **Unsafe Modifications:** DELETE/UPDATE without WHERE
- **Statement Stacking:** Multiple queries with `;`
- **Union Injection:** Suspicious UNION patterns

#### ⚠️ Warnings
- SELECT without LIMIT
- Excessive JOINs (>4)
- Deep nested subqueries (>3)
- Non-whitelisted tables

#### Configuration

```python
validator = QuerySecurityValidator(
    allowed_tables=[
        'trends.*',           # All tables in trends schema
        'pharmacies',         # Specific table
        'bookings.active_*'   # Pattern matching
    ]
)

# Limits (customizable via subclass)
validator.MAX_ROWS = 1000           # Maximum rows per query
validator.MAX_JOINS = 4             # Maximum JOIN operations
validator.MAX_QUERY_LENGTH = 5000   # Maximum query length
```

---

### MongoDB Validator

#### ✅ Safe Operations
- Standard query operators ($eq, $gt, $in, etc.)
- Safe regex (without ReDoS patterns)
- Aggregation pipelines (up to 10 stages)
- $lookup (with warnings for >3)

#### ❌ Blocked Operations
- **JavaScript Execution:** $where, $function, $accumulator
- **ReDoS Patterns:** (a+)+, (.*)*, nested quantifiers
- **Excessive Nesting:** >5 levels deep
- **Long Regex:** >200 characters
- **Large Pipelines:** >10 stages
- **Non-whitelisted Collections**

#### ⚠️ Warnings
- Multiple $lookup operations (>3)
- Large arrays (>1000 elements)
- Deep nesting (3-5 levels)

#### Configuration

```python
validator = MongoQuerySecurityValidator(
    allowed_collections=[
        'pharmacies',
        'bookings',
        'items',
        'users'
    ]
)

# Limits (customizable via subclass)
validator.MAX_PIPELINE_STAGES = 10
validator.MAX_REGEX_LENGTH = 200
validator.MAX_ARRAY_SIZE = 1000
validator.MAX_NESTING_DEPTH = 5
```

---

## 🎯 Integration Examples

### With Flask API

```python
from flask import Flask, request, jsonify
from infrastructure.security import QuerySecurityValidator

app = Flask(__name__)
validator = QuerySecurityValidator()

@app.route('/api/query', methods=['POST'])
def execute_query():
    query = request.json.get('query')

    # Validate
    result = validator.validate(query)

    if not result.is_safe:
        return jsonify({
            'error': 'Query rejected',
            'reasons': result.blocked_reasons,
            'risk_level': result.risk_level.value
        }), 400

    # Enforce row limit
    query = validator.enforce_row_limit(query)

    # Execute safely
    results = execute_sql(query)

    return jsonify({'results': results})
```

### With ChatGPT Repository

```python
from infrastructure.repositories import ChatGPTLLMRepository
from infrastructure.security import MongoQuerySecurityValidator
from infrastructure.llm import parse_llm_json

class SecureChatGPTRepository(ChatGPTLLMRepository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_validator = MongoQuerySecurityValidator()

    async def generate_query(self, question: str, *args, **kwargs):
        # Generate query using GPT
        query_spec = await super().generate_query(question, *args, **kwargs)

        # Parse GPT response
        try:
            parsed = parse_llm_json(query_spec.query, safe=True)

            if parsed and isinstance(parsed, dict):
                # Validate MongoDB query
                result = self.mongo_validator.validate_query(
                    parsed,
                    collection=query_spec.collection
                )

                if not result.is_safe:
                    raise ValueError(f"Generated unsafe query: {result.blocked_reasons}")

        except Exception as e:
            logger.error(f"Query validation failed: {e}")
            raise

        return query_spec
```

### With Query Router

```python
from infrastructure.security import (
    QuerySecurityValidator,
    MongoQuerySecurityValidator
)

class SecureQueryRouter:
    def __init__(self):
        self.sql_validator = QuerySecurityValidator()
        self.mongo_validator = MongoQuerySecurityValidator()

    def route_and_validate(self, query, database_type):
        if database_type == 'mysql':
            result = self.sql_validator.validate(query)
        else:
            result = self.mongo_validator.validate_query(query)

        if not result.is_safe:
            raise SecurityError(
                f"Query validation failed: {result.blocked_reasons}"
            )

        return query
```

---

## 🧪 Testing

Run the test suites:

```bash
# SQL validator tests
pytest tests/test_query_security.py -v

# MongoDB validator tests
pytest tests/test_mongodb_security.py -v

# LLM parser tests
pytest tests/test_llm_parser.py -v

# All security tests
pytest tests/test_*security*.py -v

# With coverage
pytest tests/test_*security*.py --cov=infrastructure.security
```

### Performance Benchmarks

All validators are designed for <5ms validation time:

```python
import time

validator = QuerySecurityValidator()
query = "SELECT * FROM products WHERE active = 1 LIMIT 100"

start = time.time()
for _ in range(100):
    validator.validate(query)
elapsed = time.time() - start

print(f"Average: {elapsed / 100 * 1000:.2f}ms per validation")
# Expected: < 5ms
```

---

## 🔧 Advanced Usage

### Custom Validator

```python
from infrastructure.security import QuerySecurityValidator

class StrictSQLValidator(QuerySecurityValidator):
    # Override limits
    MAX_ROWS = 100  # More restrictive
    MAX_JOINS = 2

    def __init__(self):
        super().__init__(allowed_tables=['public.users', 'public.orders'])

    def validate(self, query: str):
        # Add custom validation
        if 'UNION' in query.upper():
            return ValidationResult.blocked(
                ["UNION operations not allowed"],
                RiskLevel.HIGH
            )

        return super().validate(query)
```

### Sanitization (Use with Caution)

```python
validator = MongoQuerySecurityValidator()

# Dangerous query
query = {
    "active": 1,
    "$where": "this.price > 100"  # Dangerous!
}

# Sanitize (removes dangerous operators)
sanitized = validator.sanitize_query(query)
# Result: {"active": 1}

# Note: Validation should be primary defense
# Sanitization may alter query semantics
```

### Validation Result Inspection

```python
result = validator.validate(query)

# Check safety
if result.is_safe:
    print("Safe to execute")

# Risk level
print(f"Risk: {result.risk_level.value}")
# SAFE, LOW, MEDIUM, HIGH, CRITICAL

# Reasons
if result.blocked_reasons:
    for reason in result.blocked_reasons:
        print(f"  - {reason}")

# Warnings (non-blocking)
if result.warnings:
    for warning in result.warnings:
        print(f"  ⚠️ {warning}")
```

---

## 📊 Logging

Validators log security events:

```python
import logging

# Enable logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('infrastructure.security')

# Validation events are automatically logged:
# - WARNING: Blocked queries
# - INFO: Queries with warnings
# - DEBUG: Safe queries (if debug enabled)
```

---

## 🚨 Security Best Practices

1. **Always Validate Before Execution**
   ```python
   result = validator.validate(query)
   if not result.is_safe:
       raise SecurityError("Query rejected")
   # Only execute after validation
   execute_query(query)
   ```

2. **Use Whitelisting**
   ```python
   # Whitelist tables/collections explicitly
   validator = QuerySecurityValidator(
       allowed_tables=['known_table1', 'known_table2']
   )
   ```

3. **Enforce Limits**
   ```python
   # Always enforce row limits
   query = validator.enforce_row_limit(query)
   ```

4. **Log Security Events**
   ```python
   if not result.is_safe:
       logger.warning(f"Blocked query from user {user_id}: {result.blocked_reasons}")
   ```

5. **Defense in Depth**
   ```python
   # Layer multiple security measures:
   # 1. Validate with security validator
   # 2. Use parameterized queries
   # 3. Apply database-level permissions
   # 4. Monitor query execution
   ```

6. **Handle Validation Errors Gracefully**
   ```python
   try:
       result = validator.validate(query)
       if not result.is_safe:
           return user_friendly_error_message()
   except Exception as e:
       logger.error(f"Validation error: {e}")
       return generic_error_message()
   ```

---

## 📚 API Reference

### ValidationResult

```python
@dataclass
class ValidationResult:
    is_safe: bool                    # Whether query is safe
    risk_level: RiskLevel            # SAFE, LOW, MEDIUM, HIGH, CRITICAL
    blocked_reasons: List[str]       # Why query was blocked
    warnings: List[str]              # Non-blocking warnings
    sanitized_query: Optional[str]   # Sanitized version (if applicable)
```

### QuerySecurityValidator

```python
def validate(query: str) -> ValidationResult:
    """Validate SQL query for security issues."""

def enforce_row_limit(query: str) -> str:
    """Enforce maximum row limit on SELECT queries."""
```

### MongoQuerySecurityValidator

```python
def validate_query(query: Any, collection: Optional[str] = None) -> ValidationResult:
    """Validate MongoDB find query."""

def validate_pipeline(pipeline: Any, collection: Optional[str] = None) -> ValidationResult:
    """Validate MongoDB aggregation pipeline."""

def sanitize_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """Remove dangerous operators from query (use with caution)."""
```

### LLMResponseParser

```python
def parse_json(response: str, model: Optional[Type[T]] = None) -> Union[Dict, T]:
    """Parse LLM response with fallbacks. Raises ParseError on failure."""

def parse_json_safe(response: str, default: Any = None) -> Any:
    """Parse LLM response. Returns default on failure (no exception)."""

def extract_text_fallback(response: str) -> str:
    """Extract clean text from response (ultimate fallback)."""
```

---

## 🐛 Troubleshooting

### Query Blocked Unexpectedly

**Issue:** Valid query is being blocked

**Solutions:**
1. Check if table is in whitelist
2. Review query complexity limits
3. Check for string literals that match keywords
4. Enable debug logging to see exact reason

```python
import logging
logging.basicConfig(level=logging.DEBUG)
result = validator.validate(query)
```

### Performance Issues

**Issue:** Validation is slow

**Solutions:**
1. Check query length (should be <5000 chars)
2. Reduce regex complexity
3. Profile validation:
   ```python
   import cProfile
   cProfile.run('validator.validate(query)')
   ```

### Parse Errors

**Issue:** LLM response fails to parse

**Solutions:**
1. Check original response format
2. Review ParseError.attempts to see what was tried
3. Use safe mode to avoid exceptions
4. Extract text fallback as last resort

---

## 📝 Changelog

### v1.0.0 (2025-01-13)
- Initial release
- SQL query validator
- MongoDB query validator
- LLM response parser
- Comprehensive test suites
- Performance optimizations (<5ms validation)

---

## 🤝 Contributing

When adding new security checks:

1. Add detection logic to validator
2. Add corresponding test cases
3. Update documentation
4. Ensure <5ms performance target
5. Log security events appropriately

---

## 📄 License

Part of TrendsPro/Luda Mind project (MIT License)

---

**Built with security in mind. 🔒**
