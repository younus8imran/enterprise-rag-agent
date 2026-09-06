# Evaluation Strategy

This document outlines the evaluation framework for the Enterprise Intelligence Agent, designed to provide a reproducible, quantitative measure of system performance across RAG, SQL, and Web Research capabilities.

## 1. Evaluation Objectives
The primary goal is to ensure that the agentic orchestration is precise, secure, and faithful to the retrieved evidence. We focus on four key dimensions:
- **Retrieval Quality**: Did we find the right information?
- **Generation Quality**: Is the answer faithful to the context and relevant to the query?
- **Orchestration Precision**: Did the agent use the correct tools and avoid unnecessary calls?
- **Security Robustness**: Does the system block prompt injections and enforce access levels?

## 2. Benchmark Dataset
The system is evaluated against a curated benchmark dataset (`tests/evaluation/benchmark_dataset.py`) covering:
- **Simple/Difficult RAG**: Basic and nuanced internal document retrieval.
- **Multi-hop RAG**: Questions requiring synthesis across multiple documents.
- **SQL**: Precise data extraction from the enterprise database.
- **Web Research**: External knowledge gathering via search providers.
- **Hybrid**: Queries requiring the coordination of $\geq 2$ tools.
- **Edge Cases**: Unanswerable questions and adversarial prompt injections.

## 3. Metrics Framework

### Retrieval Metrics
| Metric | Description | Calculation |
| :--- | :--- | :--- |
| **Hit Rate** | % of queries that retrieved $\geq 1$ relevant doc. | $\frac{\text{Hits}}{\text{Total Queries}}$ |
| **Context Precision** | Proportion of retrieved docs that are relevant. | $\frac{\text{Relevant Docs}}{\text{Total Retrieved}}$ |
| **Context Recall** | Proportion of all relevant docs that were retrieved. | $\frac{\text{Retrieved Relevant}}{\text{Total Relevant}}$ |

### Generation Metrics (RAGAS based)
- **Faithfulness**: Measure of how much the answer is derived solely from the retrieved context.
- **Answer Relevance**: How well the answer addresses the user's original question.
- **Citation Correctness**: Verification that every claim is backed by a valid citation.

### Agentic Metrics
- **Tool Selection Accuracy**: Ratio of correct tool calls to total tool calls.
- **Task Completion Rate**: % of queries that resulted in a valid, cited answer.
- **Unnecessary Tool Calls**: Count of tools called that did not contribute to the final answer.

### SQL Metrics
- **SQL Validity**: % of generated SQL that passes the `SQLValidator`.
- **Execution Success**: % of SQL queries that run without database errors.
- **Answer Correctness**: Comparison of SQL results against ground truth values.

## 4. Evaluation Pipeline
The evaluation is triggered via `make evaluate`, which executes the following flow:
1. **Initialization**: Load the benchmark dataset and initialize the Agent Graph.
2. **Execution**: Run every benchmark question through the `AgentEvaluationRunner`.
3. **Metrics Computation**: Apply `AgentEvaluator` and `RetrievalEvaluator` to the resulting states.
4. **Reporting**: Generate a timestamped JSON report in `docs/evaluation-results/` and print a summary to the terminal.

## 5. Reproducibility
To ensure results are not fabricated:
- All metrics are computed directly from the agent's `AgentState` at the end of the run.
- Raw results (including the full state and agent traces) are saved in the JSON report.
- The same benchmark version is used across all iterations to track progress.
