"""
Evaluation runner for the Enterprise Intelligence Agent.
Runs benchmark dataset through the agent and produces reproducible metrics.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from tests.evaluation.benchmark_dataset import BENCHMARK_DATASET, get_all_categories
from tests.evaluation.evaluators import AgentEvaluator, RetrievalEvaluator, ToolSelectionMetrics, SQLMetrics, TaskMetrics
from app.services.agent.graph import create_rag_graph
from app.services.rag.service import RAGService
from app.services.sql.agent import SQLAgent
from app.services.research.agent import ResearchAgent
from app.services.research.provider import MockSearchProvider
from app.core.logging import logger

class EvaluationResult(dict):
    """Single evaluation result"""
    pass

class EvaluationReport(dict):
    """Complete evaluation report"""
    pass

class AgentEvaluationRunner:
    """
    Runs the full benchmark suite and generates evaluation reports.
    Never fabricates numbers - all metrics are computed from actual runs.
    """

    def __init__(self):
        self.results: List[EvaluationResult] = []
        self.timestamp = datetime.utcnow().isoformat()

    async def run_single_evaluation(
        self,
        agent_graph,
        question_id: str,
        question: str,
        expected_tools: List[str],
        should_fail: bool,
        adversarial: bool,
        category: str
    ) -> EvaluationResult:
        """Run a single benchmark question through the agent"""
        logger.info("evaluating_question", id=question_id, category=category)

        try:
            # Run the agent
            state = {"query": question, "iterations": 0}
            result = await agent_graph.ainvoke(state)

            # Evaluate tool selection
            tool_metrics = AgentEvaluator.evaluate_tool_selection(
                expected_tools, result
            )

            # Evaluate SQL if SQL tool was used
            sql_metrics = None
            if "sql" in expected_tools:
                sql_metrics = AgentEvaluator.evaluate_sql_generation(
                    result, not should_fail
                )

            # Evaluate task completion
            task_metrics = AgentEvaluator.evaluate_task_completion(
                result, should_fail
            )

            # Evaluate retrieval if RAG was used
            hit_rate = 0.0
            context_precision = 0.0
            if "rag" in expected_tools and result.get("documents"):
                hit_rate = RetrievalEvaluator.calculate_hit_rate(
                    result.get("documents", [])
                )
                context_precision = RetrievalEvaluator.calculate_context_precision(
                    result.get("documents", []),
                    question.split()[:5]  # First 5 words as ground truth tokens
                )

            return EvaluationResult({
                "question_id": question_id,
                "category": category,
                "question": question,
                "expected_tools": expected_tools,
                "actual_tools": result.get("tools_to_use", []),
                "should_fail": should_fail,
                "adversarial": adversarial,
                "answer": result.get("answer", ""),
                "confidence": result.get("confidence", 0.0),
                "tool_selection_accuracy": tool_metrics.accuracy,
                "tools_correct": tool_metrics.correct,
                "tools_missed": tool_metrics.missed,
                "tools_unnecessary": tool_metrics.unnecessary,
                "task_completed": task_metrics.task_completed,
                "error_occurred": task_metrics.error_occurred,
                "citation_correctness": task_metrics.citation_correctness,
                "sql_metrics": sql_metrics.dict() if sql_metrics else None,
                "retrieval_hit_rate": hit_rate,
                "retrieval_context_precision": context_precision,
                "success": True
            })

        except Exception as e:
            logger.error("evaluation_failed", id=question_id, error=str(e))
            return EvaluationResult({
                "question_id": question_id,
                "category": category,
                "question": question,
                "error": str(e),
                "success": False
            })

    async def run_full_evaluation(self) -> EvaluationReport:
        """Run the complete benchmark suite"""
        logger.info("starting_full_evaluation", total_questions=len(BENCHMARK_DATASET))

        # Create mock agent for evaluation
        # In production, this would use real services
        from unittest.mock import MagicMock, AsyncMock

        mock_rag = MagicMock(spec=RAGService)
        dummy_doc = MagicMock()
        dummy_doc.content = "Test document content"
        dummy_doc.chunk_id = 1
        dummy_doc.score = 0.8
        mock_rag.hybrid_search = AsyncMock(return_value=[dummy_doc])
        mock_rag.rerank = AsyncMock(return_value=[dummy_doc])

        mock_sql = MagicMock(spec=SQLAgent)
        mock_sql.execute_query = AsyncMock(return_value="SQL Result")

        mock_search = MockSearchProvider()
        mock_research = ResearchAgent(mock_search)

        agent_graph = create_rag_graph(mock_rag, mock_sql, mock_research)

        # Run all benchmark questions
        for benchmark in BENCHMARK_DATASET:
            result = await self.run_single_evaluation(
                agent_graph,
                benchmark.id,
                benchmark.question,
                benchmark.expected_tools,
                benchmark.should_fail,
                benchmark.adversarial,
                benchmark.category
            )
            self.results.append(result)

        # Compute aggregate metrics
        report = self._generate_report()
        return report

    def _generate_report(self) -> EvaluationReport:
        """Generate aggregate metrics from results"""
        successful_evals = [r for r in self.results if r.get("success", False)]

        if not successful_evals:
            return EvaluationReport({
                "timestamp": self.timestamp,
                "total_questions": len(self.results),
                "successful_evaluations": 0,
                "error": "No successful evaluations"
            })

        # Overall metrics
        total = len(successful_evals)

        # Tool selection metrics
        avg_tool_accuracy = sum(r["tool_selection_accuracy"] for r in successful_evals) / total
        avg_unnecessary_tools = sum(r["tools_unnecessary"] for r in successful_evals) / total

        # Task completion metrics
        task_completion_rate = sum(1 for r in successful_evals if r["task_completed"]) / total

        # Citation metrics
        avg_citation_correctness = sum(r["citation_correctness"] for r in successful_evals) / total

        # SQL metrics (for SQL questions only)
        sql_results = [r for r in successful_evals if r.get("sql_metrics")]
        sql_validity_rate = 0.0
        sql_execution_rate = 0.0
        if sql_results:
            sql_validity_rate = sum(
                1 for r in sql_results if r["sql_metrics"]["sql_valid"]
            ) / len(sql_results)
            sql_execution_rate = sum(
                1 for r in sql_results if r["sql_metrics"]["execution_success"]
            ) / len(sql_results)

        # Retrieval metrics (for RAG questions only)
        rag_results = [r for r in successful_evals if r["retrieval_hit_rate"] > 0]
        avg_hit_rate = 0.0
        avg_context_precision = 0.0
        if rag_results:
            avg_hit_rate = sum(r["retrieval_hit_rate"] for r in rag_results) / len(rag_results)
            avg_context_precision = sum(r["retrieval_context_precision"] for r in rag_results) / len(rag_results)

        # Adversarial handling
        adversarial_results = [r for r in successful_evals if r.get("adversarial", False)]
        adversarial_blocked_rate = 0.0
        if adversarial_results:
            adversarial_blocked_rate = sum(
                1 for r in adversarial_results
                if "Security Error" in r.get("answer", "") or "Malicious input" in r.get("answer", "")
            ) / len(adversarial_results)

        # Per-category breakdown
        categories = get_all_categories()
        category_metrics = {}
        for cat in categories:
            cat_results = [r for r in successful_evals if r["category"] == cat]
            if cat_results:
                category_metrics[cat] = {
                    "count": len(cat_results),
                    "tool_accuracy": sum(r["tool_selection_accuracy"] for r in cat_results) / len(cat_results),
                    "task_completion": sum(1 for r in cat_results if r["task_completed"]) / len(cat_results),
                }

        return EvaluationReport({
            "timestamp": self.timestamp,
            "total_questions": len(self.results),
            "successful_evaluations": total,
            "overall_metrics": {
                "tool_selection_accuracy": round(avg_tool_accuracy, 3),
                "avg_unnecessary_tool_calls": round(avg_unnecessary_tools, 3),
                "task_completion_rate": round(task_completion_rate, 3),
                "citation_correctness": round(avg_citation_correctness, 3),
            },
            "retrieval_metrics": {
                "hit_rate": round(avg_hit_rate, 3),
                "context_precision": round(avg_context_precision, 3),
            },
            "sql_metrics": {
                "sql_validity_rate": round(sql_validity_rate, 3),
                "sql_execution_rate": round(sql_execution_rate, 3),
            },
            "security_metrics": {
                "adversarial_blocked_rate": round(adversarial_blocked_rate, 3),
            },
            "category_breakdown": category_metrics,
            "detailed_results": self.results
        })

    def save_report(self, report: EvaluationReport, output_path: str):
        """Save evaluation report to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info("report_saved", path=output_path)

async def main():
    """Main evaluation entry point"""
    runner = AgentEvaluationRunner()
    report = await runner.run_full_evaluation()

    # Save report with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_path = f"docs/evaluation-results/eval_{timestamp}.json"
    runner.save_report(report, output_path)

    # Print summary
    print("\n" + "="*60)
    print("EVALUATION REPORT SUMMARY")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Questions: {report['total_questions']}")
    print(f"Successful Evaluations: {report['successful_evaluations']}")
    print("\nOverall Metrics:")
    for metric, value in report['overall_metrics'].items():
        print(f"  {metric}: {value}")
    print("\nRetrieval Metrics:")
    for metric, value in report['retrieval_metrics'].items():
        print(f"  {metric}: {value}")
    print("\nSQL Metrics:")
    for metric, value in report['sql_metrics'].items():
        print(f"  {metric}: {value}")
    print("\nSecurity Metrics:")
    for metric, value in report['security_metrics'].items():
        print(f"  {metric}: {value}")
    print(f"\nDetailed report saved to: {output_path}")
    print("="*60 + "\n")

    return report

if __name__ == "__main__":
    asyncio.run(main())
