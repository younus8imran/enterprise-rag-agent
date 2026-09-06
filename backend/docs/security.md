# Enterprise Security Architecture

This document describes the security model for the Enterprise Intelligence Agent, focusing on the zero-trust approach to LLM-generated inputs and tool outputs.

## 1. Authentication & Identity
The system uses a multi-tenant identity model:
- **User Identity**: Each request is associated with a `UserIdentity` containing `user_id`, `role`, `tenant_id`, and `access_level`.
- **Identity Context**: An `AuthContext` is propagated through the agentic loop to ensure every tool call is performed on behalf of a verified identity.

## 2. Authorization & Access Control
Access is governed by a combination of Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC):

### Tool Permissions
Access to specific agents/tools is restricted by role:
- **SQL Agent**: Restricted to `admin` and `manager`.
- **Internal RAG**: Available to all authenticated employees.
- **Web Research**: Available to all authenticated employees.

### Document Access Levels
The system implements fine-grained document security via metadata filtering:
- **Tenant Isolation**: Documents are filtered by `tenant_id` to ensure data isolation.
- **Access Level**: Documents have an `access_level` (1: Basic, 2: Confidential, 3: Top Secret). Users can only retrieve documents where `doc.access_level <= user.access_level`.

## 3. Defense-in-Depth for LLMs

### Prompt Injection Defenses
The system treats all user input as potentially malicious:
- **Input Validation**: All queries are scanned for known injection patterns (e.g., "ignore previous instructions", "reveal system prompt") using `SecurityValidator`.
- **Input Sanitization**: Malicious inputs are blocked before they reach the agentic orchestration layer.

### Untrusted Data Handling
The system adopts a "Treat as Untrusted" policy for three primary data streams:
1. **Retrieved Documents**: Filtered via `AccessControl` before being passed to the LLM.
2. **Web Pages**: Content is sanitized via `SecurityValidator.sanitize_output` to prevent XSS and injection.
3. **Tool Outputs**: SQL and API results are validated against expected schemas before being integrated into the final answer.

## 4. SQL Security
To prevent SQL injection and unauthorized data modification:
- **Read-Only Roles**: The SQL agent connects via a database user with strictly `SELECT` permissions.
- **Parameterized Queries**: Use of parameterized queries is mandatory; raw f-string SQL is forbidden.
- **keyword Filtering**: A final safety check (`SecurityValidator.validate_sql`) blocks dangerous keywords like `DROP`, `DELETE`, or `UPDATE`.

## 5. Validation Pipeline
Every interaction follows this security pipeline:
`User Input` $\rightarrow$ `Injection Check` $\rightarrow$ `Identity Verification` $\rightarrow$ `Tool Authorization` $\rightarrow$ `Metadata Filtering` $\rightarrow$ `Output Sanitization` $\rightarrow$ `Final Answer`
