"""
Prompt Manager Service

Centralized management of system prompts for LLM interactions.
Follows Single Responsibility Principle - only manages prompts.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class PromptCategory(str, Enum):
    """Categories of prompts in the system."""
    QUERY_GENERATION = "query_generation"
    ANSWER_GENERATION = "answer_generation"
    INTENT_ANALYSIS = "intent_analysis"
    ERROR_HANDLING = "error_handling"
    ROUTING = "routing"
    VALIDATION = "validation"
    BUSINESS = "business"
    TECHNICAL = "technical"


class PromptTemplate:
    """
    Represents a prompt template with metadata.

    Encapsulates prompt content, variables, and versioning.
    """

    def __init__(self,
                 name: str,
                 content: str,
                 category: PromptCategory,
                 variables: Optional[List[str]] = None,
                 description: str = "",
                 version: str = "1.0.0",
                 tags: Optional[List[str]] = None):
        """
        Initialize prompt template.

        Args:
            name: Template name
            content: Template content with {variable} placeholders
            category: Prompt category
            variables: List of variable names in template
            description: Template description
            version: Template version
            tags: Optional tags for categorization
        """
        self.name = name
        self.content = content
        self.category = category
        self.variables = variables or self._extract_variables(content)
        self.description = description
        self.version = version
        self.tags = tags or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.usage_count = 0

    def _extract_variables(self, content: str) -> List[str]:
        """Extract variable names from template content."""
        import re
        pattern = r'\{(\w+)\}'
        return list(set(re.findall(pattern, content)))

    def format(self, **kwargs) -> str:
        """
        Format template with provided variables.

        Args:
            **kwargs: Variable values

        Returns:
            Formatted prompt

        Raises:
            KeyError: If required variable is missing
        """
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise KeyError(f"Missing required variables: {missing}")

        self.usage_count += 1
        return self.content.format(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'content': self.content,
            'category': self.category.value,
            'variables': self.variables,
            'description': self.description,
            'version': self.version,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'usage_count': self.usage_count
        }


class PromptManager:
    """
    Manages all system prompts centrally.

    Provides a single source of truth for all prompts used in the system,
    supporting versioning, categorization, and dynamic loading.
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize prompt manager.

        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = prompts_dir or Path("prompts")
        self._templates: Dict[str, PromptTemplate] = {}
        self._categories: Dict[PromptCategory, List[str]] = {
            category: [] for category in PromptCategory
        }

        # Load default prompts
        self._load_default_prompts()

        # Load from files if directory exists
        if self.prompts_dir.exists():
            self._load_from_directory()

    def _load_default_prompts(self):
        """Load default system prompts."""

        # Query generation prompts
        self.register_template(
            name="mysql_query_generation",
            content="""You are an expert MySQL query generator.

Task: Convert this natural language question into a MySQL query.
Question: {question}

Database Schema:
{schema}

Requirements:
- Generate only SELECT queries (no modifications)
- Use proper JOIN syntax when needed
- Include appropriate WHERE clauses
- Add ORDER BY and LIMIT as needed
- Default to LIMIT 100 if not specified

Return a JSON object with:
- query: The SQL query
- explanation: Brief explanation of the query
- tables_used: List of tables referenced""",
            category=PromptCategory.QUERY_GENERATION,
            description="Generate MySQL queries from natural language"
        )

        self.register_template(
            name="mongodb_query_generation",
            content="""You are an expert MongoDB query generator.

Task: Convert this natural language question into a MongoDB query.
Question: {question}

Collections Available:
{collections}

Requirements:
- Generate find() or aggregate() queries only
- Use proper filter syntax
- Include projection when needed
- Add sort and limit options
- Default to limit: 100 if not specified

Return a JSON object with:
- collection: Target collection name
- operation: "find" or "aggregate"
- query: The query/pipeline
- options: Additional options (sort, limit, projection)""",
            category=PromptCategory.QUERY_GENERATION,
            description="Generate MongoDB queries from natural language"
        )

        # Answer generation prompts
        self.register_template(
            name="technical_answer",
            content="""You are a technical assistant explaining database results.

Question: {question}
Results: {results}
Query Executed: {query}

Provide a clear, technical explanation of the results.
Include:
- Summary of findings
- Key insights
- Any patterns or anomalies
- Technical details when relevant

Keep the response concise and factual.""",
            category=PromptCategory.ANSWER_GENERATION,
            description="Generate technical answers from query results"
        )

        self.register_template(
            name="business_answer_spanish",
            content="""Eres un asistente de análisis de datos para el equipo de negocio.

Pregunta: {question}
Resultados: {results}
Contexto de Negocio: {context}

Proporciona una respuesta clara y orientada a negocio en español.
Incluye:
- Resumen ejecutivo
- Insights clave para decisiones
- Recomendaciones si aplica
- Formato amigable (bullets, negritas)

Responde siempre en español de manera profesional pero accesible.""",
            category=PromptCategory.ANSWER_GENERATION,
            description="Generate business-oriented answers in Spanish"
        )

        # Intent analysis prompts
        self.register_template(
            name="query_intent_analysis",
            content="""Analyze the intent of this database query request.

Question: {question}

Determine:
1. Query type: analytics, operational, reporting, lookup, aggregation
2. Entities involved: products, users, sales, pharmacies, etc.
3. Time range: specific dates, relative periods, or none
4. Required aggregations: sum, avg, count, etc.
5. Suggested database: MySQL (analytics) or MongoDB (operational)
6. Confidence level: 0.0 to 1.0

Return a JSON object with all findings.""",
            category=PromptCategory.INTENT_ANALYSIS,
            description="Analyze query intent and requirements"
        )

        # Routing prompts
        self.register_template(
            name="database_routing",
            content="""Determine the appropriate database for this query.

Question: {question}

MySQL indicators: {mysql_keywords}
MongoDB indicators: {mongodb_keywords}

Rules:
- MySQL: analytics, trends, historical data, sales analysis
- MongoDB: current operations, real-time data, user/pharmacy info

Return: "mysql" or "mongodb" with confidence score.""",
            category=PromptCategory.ROUTING,
            description="Route queries to appropriate database"
        )

        # Error handling prompts
        self.register_template(
            name="error_explanation",
            content="""Explain this database error to the user.

Error Type: {error_type}
Error Message: {error_message}
Query Attempted: {query}
Language: {language}

Provide a clear, helpful explanation of:
- What went wrong
- Why it might have happened
- Suggested fixes or alternatives

Keep it user-friendly, not too technical.""",
            category=PromptCategory.ERROR_HANDLING,
            description="Explain database errors to users"
        )

        # Business-specific prompts
        self.register_template(
            name="partner_gmv_analysis",
            content="""Analiza el GMV del partner para el equipo de negocio.

Partner: {partner}
Período: {time_range}
Datos: {data}

Proporciona:
1. GMV total y tendencia
2. Comparación con período anterior si hay datos
3. Productos top del partner
4. Insights sobre el rendimiento
5. Recomendaciones estratégicas

Formato ejecutivo, usa € para montos.""",
            category=PromptCategory.BUSINESS,
            description="Analyze partner GMV for business team"
        )

        self.register_template(
            name="risk_analysis",
            content="""Analyze products at risk based on Z_Y scores.

Products with Z_Y < -0.30: {critical_products}
Products with Z_Y < 0: {at_risk_products}

Provide:
1. Risk summary by category
2. Critical products requiring immediate action
3. Trend analysis if historical data available
4. Recommended actions for each risk level

Be specific and actionable.""",
            category=PromptCategory.BUSINESS,
            description="Analyze product risk from Z_Y scores"
        )

        logger.info(f"Loaded {len(self._templates)} default prompts")

    def register_template(self,
                         name: str,
                         content: str,
                         category: PromptCategory,
                         **kwargs) -> PromptTemplate:
        """
        Register a new prompt template.

        Args:
            name: Template name (must be unique)
            content: Template content
            category: Template category
            **kwargs: Additional template parameters

        Returns:
            Created PromptTemplate

        Raises:
            ValueError: If template name already exists
        """
        if name in self._templates:
            raise ValueError(f"Template '{name}' already exists")

        template = PromptTemplate(
            name=name,
            content=content,
            category=category,
            **kwargs
        )

        self._templates[name] = template
        self._categories[category].append(name)

        logger.debug(f"Registered template: {name} ({category.value})")
        return template

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a template by name.

        Args:
            name: Template name

        Returns:
            PromptTemplate or None if not found
        """
        return self._templates.get(name)

    def get_prompt(self, name: str, **variables) -> str:
        """
        Get a formatted prompt.

        Args:
            name: Template name
            **variables: Template variables

        Returns:
            Formatted prompt

        Raises:
            KeyError: If template not found or variables missing
        """
        template = self.get_template(name)
        if not template:
            raise KeyError(f"Template '{name}' not found")

        return template.format(**variables)

    def get_by_category(self, category: PromptCategory) -> List[PromptTemplate]:
        """
        Get all templates in a category.

        Args:
            category: Prompt category

        Returns:
            List of templates
        """
        names = self._categories.get(category, [])
        return [self._templates[name] for name in names if name in self._templates]

    def get_by_tags(self, tags: List[str]) -> List[PromptTemplate]:
        """
        Get templates matching any of the provided tags.

        Args:
            tags: List of tags to match

        Returns:
            List of matching templates
        """
        matching = []
        for template in self._templates.values():
            if any(tag in template.tags for tag in tags):
                matching.append(template)
        return matching

    def update_template(self,
                       name: str,
                       content: Optional[str] = None,
                       version: Optional[str] = None,
                       **kwargs):
        """
        Update an existing template.

        Args:
            name: Template name
            content: New content (optional)
            version: New version (optional)
            **kwargs: Other fields to update

        Raises:
            KeyError: If template not found
        """
        template = self.get_template(name)
        if not template:
            raise KeyError(f"Template '{name}' not found")

        if content:
            template.content = content
            template.variables = template._extract_variables(content)

        if version:
            template.version = version

        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.now()
        logger.info(f"Updated template: {name} (v{template.version})")

    def _load_from_directory(self):
        """Load prompts from directory."""
        for file_path in self.prompts_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Handle single or multiple prompts in file
                    prompts = data if isinstance(data, list) else [data]

                    for prompt_data in prompts:
                        category = PromptCategory(prompt_data.get('category', 'technical'))
                        self.register_template(
                            name=prompt_data['name'],
                            content=prompt_data['content'],
                            category=category,
                            description=prompt_data.get('description', ''),
                            version=prompt_data.get('version', '1.0.0'),
                            tags=prompt_data.get('tags', [])
                        )

                logger.info(f"Loaded prompts from {file_path.name}")

            except Exception as e:
                logger.error(f"Failed to load prompts from {file_path}: {e}")

    def save_to_directory(self):
        """Save all prompts to directory."""
        if not self.prompts_dir.exists():
            self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Group by category for organization
        for category in PromptCategory:
            templates = self.get_by_category(category)
            if not templates:
                continue

            file_path = self.prompts_dir / f"{category.value}.json"
            data = [template.to_dict() for template in templates]

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(templates)} prompts to {file_path.name}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics for prompts.

        Returns:
            Statistics dictionary
        """
        total_usage = sum(t.usage_count for t in self._templates.values())
        most_used = max(self._templates.values(), key=lambda t: t.usage_count) if self._templates else None

        return {
            'total_templates': len(self._templates),
            'by_category': {
                cat.value: len(self.get_by_category(cat))
                for cat in PromptCategory
            },
            'total_usage': total_usage,
            'most_used': most_used.name if most_used else None,
            'most_used_count': most_used.usage_count if most_used else 0,
            'average_usage': total_usage / len(self._templates) if self._templates else 0
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"PromptManager(templates={len(self._templates)}, categories={len(self._categories)})"


# Singleton instance
_prompt_manager_instance = None


def get_prompt_manager() -> PromptManager:
    """
    Get singleton prompt manager instance.

    Returns:
        PromptManager singleton
    """
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance