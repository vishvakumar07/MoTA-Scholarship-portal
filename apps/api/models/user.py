"""
User, Role, Permission, RolePermission, UserRole, RefreshToken models.

Design principles:
  - RBAC: 6 system roles: applicant, verification_officer, scrutiny_officer, selection_committee, scheme_admin, super_admin
  - PII Protection: Aadhaar stored as SHA-256 hash ONLY
  - Security: JWT tokens with refresh token rotation
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# -------------------------------------------------------------------
# Roles
# -------------------------------------------------------------------
class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    System roles. Seeded at startup.

    Official roles:
      applicant, verification_officer, scrutiny_officer,
      selection_committee, scheme_admin, super_admin
    """

    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permissions", back_populates="roles"
    )
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")

    @property
    def roles(self) -> list["Role"]:
        if hasattr(self, "_roles_override"):
            return self._roles_override
        if hasattr(self, "user_roles") and self.user_roles:
            return [ur.role for ur in self.user_roles if getattr(ur, "role", None) is not None]
        return []

    @roles.setter
    def roles(self, value: list["Role"]):
        self._roles_override = value

    def __repr__(self) -> str:
        return f"<Role {self.code}>"


# -------------------------------------------------------------------
# Permissions
# -------------------------------------------------------------------
class Permission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Granular permission: resource:action pairs.
    Example: "applications:read", "documents:verify", "schemes:configure"
    """

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(60), nullable=False)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("resource", "action", name="uq_permission_resource_action"),)

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


# -------------------------------------------------------------------
# Role + Permission mapping
# -------------------------------------------------------------------
class RolePermission(Base):
    """Many-to-many: Role + Permission."""

    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


# -------------------------------------------------------------------
# Users
# -------------------------------------------------------------------
class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    System user account.

    Covers all roles: applicants, officers, admins.
    Role assignment is via UserRole table.
    """

    __tablename__ = "users"

    # Credentials
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Security
    # Aadhaar is stored as SHA-256 hash ONLY  -  NEVER plaintext
    aadhaar_number_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Security tracking
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Demo/test flag  -  TEST records are never real applicants
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", foreign_keys="[UserRole.user_id]", back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# -------------------------------------------------------------------
# User + Role mapping
# -------------------------------------------------------------------
class UserRole(Base, TimestampMixin):
    """
    Many-to-many: User + Role.
    Includes expiry support (for temporary role assignments).
    """

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")


# -------------------------------------------------------------------
# Refresh Tokens
# -------------------------------------------------------------------
class RefreshToken(Base, UUIDPrimaryKeyMixin):
    """
    Stored refresh tokens for JWT rotation.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        from datetime import timezone as tz
        return datetime.now(tz.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken user={self.user_id} revoked={self.is_revoked}>"
