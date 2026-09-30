"""
Applicant profile and education history models.

Security decisions:
- bank_account_number: AES-256-GCM encrypted at column level
- All bank fields encrypted together as a JSON payload
- Raw bank account number NEVER stored in plaintext
"""

from __future__ import annotations

import uuid
from datetime import date
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Gender(str, PyEnum):
    MALE = "male"
    FEMALE = "female"
    TRANSGENDER = "transgender"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class EducationLevel(str, PyEnum):
    PRE_MATRIC = "pre_matric"          # Class IX - X
    MATRIC = "matric"                   # Class X
    POST_MATRIC = "post_matric"         # Class XI - XII
    GRADUATE = "graduate"
    POST_GRADUATE = "post_graduate"
    M_PHIL = "m_phil"
    PHD = "phd"
    OTHER = "other"


#  -  - - Applicant Profile  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class ApplicantProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Extended profile for applicant-role users.

    One-to-one with User.
    Contains tribal/ST specific eligibility information.

    Bank account is stored as AES-256-GCM encrypted JSON.
    Aadhaar is NOT stored here  -  only hash on the User model.
    """

    __tablename__ = "applicant_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Personal details
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(
        SAEnum(Gender, name="gender_enum"), nullable=True
    )
    father_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    guardian_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Tribal status (core eligibility field)
    caste: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tribe_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state_of_domicile: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_pvtg: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Particularly Vulnerable Tribal Group
    is_divyangjan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Person with Disability

    # Annual family income (used for eligibility checks)
    annual_family_income: Mapped[int | None] = mapped_column(Integer, nullable=True)  # in INR

    # Contact
    address_line1: Mapped[str | None] = mapped_column(String(300), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(300), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Bank account  -  AES-256-GCM encrypted JSON
    # Contains: account_number, ifsc_code, bank_name, branch_name, account_holder_name
    # NEVER stored in plaintext
    bank_details_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Profile completion
    is_profile_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    education_records: Mapped[list["ApplicantEducation"]] = relationship(
        "ApplicantEducation", back_populates="applicant_profile"
    )

    def __repr__(self) -> str:
        return f"<ApplicantProfile user_id={self.user_id}>"


#  -  - - Applicant Education  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class ApplicantEducation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Education history entries for an applicant.
    Multiple entries allowed (one per institution/level).
    """

    __tablename__ = "applicant_education"

    applicant_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applicant_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    education_level: Mapped[EducationLevel] = mapped_column(
        SAEnum(EducationLevel, name="education_level_enum"), nullable=False
    )
    institution_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    institution_code: Mapped[str | None] = mapped_column(String(100), nullable=True)  # DISE/AISHE code
    course_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    year_of_passing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percentage_or_cgpa: Mapped[str | None] = mapped_column(String(20), nullable=True)
    board_or_university: Mapped[str | None] = mapped_column(String(200), nullable=True)
    roll_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    state_of_institution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district_of_institution: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    applicant_profile: Mapped["ApplicantProfile"] = relationship(
        "ApplicantProfile", back_populates="education_records"
    )
