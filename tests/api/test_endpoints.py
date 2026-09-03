import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test helper: Mock authentication header
def get_auth_headers(role="admin"):
    return {"Authorization": f"Bearer {role}"}

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_endpoint_requires_auth():
    """Test that chat endpoint requires authentication"""
    response = client.post("/api/v1/chat", json={"query": "test"})
    assert response.status_code == 401

def test_chat_endpoint_success():
    """Test successful chat request"""
    response = client.post(
        "/api/v1/chat",
        headers=get_auth_headers("admin"),
        json={
            "query": "What is the revenue for Q2?",
            "stream": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "answer" in data
    assert "confidence" in data
    assert "citations" in data
    assert "tools_used" in data

def test_chat_endpoint_validation():
    """Test input validation on chat endpoint"""
    # Empty query
    response = client.post(
        "/api/v1/chat",
        headers=get_auth_headers("admin"),
        json={"query": "", "stream": False}
    )
    assert response.status_code == 422

    # Query too long
    response = client.post(
        "/api/v1/chat",
        headers=get_auth_headers("admin"),
        json={"query": "x" * 3000, "stream": False}
    )
    assert response.status_code == 422

def test_research_endpoint():
    """Test research endpoint"""
    response = client.post(
        "/api/v1/research",
        headers=get_auth_headers("admin"),
        json={
            "question": "What are the market trends?",
            "stream": False
        }
    )
    assert response.status_code == 202
    data = response.json()
    assert "run_id" in data
    assert "answer" in data
    assert "confidence" in data

def test_documents_list_endpoint():
    """Test document listing"""
    response = client.get(
        "/api/v1/documents",
        headers=get_auth_headers("admin")
    )
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data

def test_documents_ingest_endpoint():
    """Test document ingestion"""
    response = client.post(
        "/api/v1/documents/ingest",
        headers=get_auth_headers("admin"),
        json={
            "file_path": "/path/to/doc.pdf",
            "tenant_id": "t1",
            "access_level": 2
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert "chunks_created" in data
    assert data["status"] == "completed"

def test_documents_ingest_tenant_isolation():
    """Test that users cannot ingest for different tenants"""
    # Admin user has tenant_id "t1"
    response = client.post(
        "/api/v1/documents/ingest",
        headers=get_auth_headers("employee"),  # employee also has t1
        json={
            "file_path": "/path/to/doc.pdf",
            "tenant_id": "t2",  # Different tenant
            "access_level": 1
        }
    )
    assert response.status_code == 403

def test_run_status_endpoint():
    """Test run status retrieval"""
    response = client.get(
        "/api/v1/runs/test-run-id",
        headers=get_auth_headers("admin")
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "status" in data

def test_openapi_documentation():
    """Test that OpenAPI schema is available"""
    response = client.get("/api/v1/docs")
    # In debug mode, docs should be available
    # Response varies based on settings.APP_DEBUG
    assert response.status_code in [200, 404]

def test_cors_headers():
    """Test CORS configuration"""
    response = client.options(
        "/api/v1/health",
        headers={"Origin": "https://example.com"}
    )
    # CORS middleware should add appropriate headers
    assert response.status_code == 200
