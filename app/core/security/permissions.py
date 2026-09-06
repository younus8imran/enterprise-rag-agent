from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.core.security.auth import UserIdentity


class AccessControl:
    """
    Implements fine-grained authorization and metadata filtering.
    """

    @staticmethod
    def filter_documents_by_access(user: UserIdentity, documents: List[Any]) -> List[Any]:
        """
        Filter retrieved documents based on user's access level and tenant.
        Treats documents as untrusted data and verifies metadata.
        """
        filtered = []
        for doc in documents:
            # Treat doc as untrusted: verify it has necessary metadata
            metadata = getattr(doc, 'metadata', {})
            if not metadata:
                continue

            # 1. Tenant Isolation
            doc_tenant = metadata.get("tenant_id")
            if doc_tenant != user.tenant_id:
                continue

            # 2. Access Level check
            doc_level = metadata.get("access_level", 1)
            if doc_level > user.access_level:
                continue

            filtered.append(doc)
        return filtered

    @staticmethod
    def validate_tool_permission(user: UserIdentity, tool_name: str) -> bool:
        """
        Checks if a user is authorized to use a specific tool.
        """
        # Admin can use anything
        if user.role == "admin":
            return True

        permissions = {
            "sql": ["admin", "manager"],
            "web": ["admin", "manager", "employee"],
            "rag": ["admin", "manager", "employee"],
        }

        allowed_roles = permissions.get(tool_name, [])
        return user.role in allowed_roles
