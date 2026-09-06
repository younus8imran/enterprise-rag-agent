"""
Custom evaluators for agent-specific metrics.
These complement RAGAS metrics for retrieval and generation quality.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.agent.state import AgentState

class ToolSelectionMetrics(BaseModel):
    """Metrics for agent tool selection accuracy"""
    expected_tools: List[str]
    actual_tools: List[str]
    correct: int = 0
    missed: int = 0
    unnecessary: int = 0
    accuracy: float = 0.0

class SQLMetrics(BaseModel):
    """Metrics for SQL generation and execution"""
    sql_generated: bool
    sql_valid: bool
    execution_success: bool
    answer_correct: bool
    contains_forbidden_keywords: bool = False

class TaskMetrics(BaseModel):
    """Overall task completion metrics"""
    task_completed: bool
    error_occurred: bool
    confidence_score: float
    answer_faithfulness: float = 0.0
    citation_correctness: float = 0.0

class AgentEvaluator:
    """Custom evaluator for agent-specific behaviors"""

    @staticmethod
    def evaluate_tool_selection(
        expected_tools: List[str],
        actual_state: Dict[str, Any]
    ) -> ToolSelectionMetrics:
        """
        Evaluate whether the agent selected the correct tools.
        """
        actual_tools = actual_state.get("tools_to_use", [])

        expected_set = set(expected_tools)
        actual_set = set(actual_tools)

        correct = len(expected_set & actual_set)
        missed = len(expected_set - actual_set)
        unnecessary = len(actual_set - expected_set)

        # Accuracy: (correct) / (correct + missed + unnecessary)
        total = correct + missed + unnecessary
        accuracy = correct / total if total > 0 else 0.0

        return ToolSelectionMetrics(
            expected_tools=expected_tools,
            actual_tools=actual_tools,
            correct=correct,
            missed=missed,
            unnecessary=unnecessary,
            accuracy=accuracy
        )

    @staticmethod
    def evaluate_sql_generation(
        state: Dict[str, Any],
        expected_success: bool
    ) -> SQLMetrics:
        """
        Evaluate SQL generation, validation, and execution.
        """
        from app.core.security.validation import SecurityValidator

        sql_results = state.get("sql_results", [])
        sql_generated = len(sql_results) > 0

        # Check if SQL was valid (no forbidden keywords)
        sql_valid = True
        contains_forbidden = False
        if sql_generated and sql_results:
            sql_text = str(sql_results[0])
            try:
                sql_valid = SecurityValidator.validate_sql(sql_text)
                contains_forbidden = not sql_valid
            except:
                sql_valid = False

        # Check execution success
        execution_success = sql_generated and sql_valid

        # Answer correctness (simplified: did we get data?)
        answer_correct = execution_success and expected_success

        return SQLMetrics(
            sql_generated=sql_generated,
            sql_valid=sql_valid,
            execution_success=execution_success,
            answer_correct=answer_correct,
            contains_forbidden_keywords=contains_forbidden
        )

    @staticmethod
    def evaluate_task_completion(
        state: Dict[str, Any],
        should_fail: bool
    ) -> TaskMetrics:
        """
        Evaluate overall task completion.
        """
        answer = state.get("answer", "")
        confidence = state.get("confidence", 0.0)

        # Task completed if we got an answer
        task_completed = len(answer) > 0

        # Error occurred if answer contains error messages
        error_occurred = any(
            err in answer
            for err in ["Error", "failed", "No evidence found"]
        )

        # If this should have failed, success = error occurred
        if should_fail:
            task_completed = error_occurred

        # Citation correctness: do we have citations?
        citations = state.get("citations", [])
        citation_correctness = 1.0 if len(citations) > 0 else 0.0

        return TaskMetrics(
            task_completed=task_completed,
            error_occurred=error_occurred,
            confidence_score=confidence,
            citation_correctness=citation_correctness
        )

class RetrievalEvaluator:
    """Evaluator for retrieval quality metrics"""

    @staticmethod
    def calculate_hit_rate(
        retrieved_docs: List[Any],
        relevant_threshold: float = 0.5
    ) -> float:
        """
        Calculate hit rate: % of queries that retrieved at least one relevant doc.
        """
        if not retrieved_docs:
            return 0.0

        # Check if at least one doc exceeds relevance threshold
        has_relevant = any(
            getattr(doc, 'score', 0) >= relevant_threshold
            for doc in retrieved_docs
        )

        return 1.0 if has_relevant else 0.0

    @staticmethod
    def calculate_context_precision(
        retrieved_docs: List[Any],
        ground_truth_tokens: List[str]
    ) -> float:
        """
        Calculate what % of retrieved docs are actually relevant.
        Simplified: check if ground truth keywords appear in retrieved content.
        """
        if not retrieved_docs or not ground_truth_tokens:
            return 0.0

        relevant_count = 0
        for doc in retrieved_docs:
            content = getattr(doc, 'content', '').lower()
            if any(token.lower() in content for token in ground_truth_tokens):
                relevant_count += 1

        return relevant_count / len(retrieved_docs)
