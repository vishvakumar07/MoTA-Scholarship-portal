"""
Pydantic v2 schemas for Applicant Profile endpoints.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


# -- Education ----------------------------------------------------------------
class EducationRecordIn(BaseModel):
    education_level: str
    institution_name: Optional[str] = None
    institution_code: Optional[str] = None
    course_name: Optional[str] = None
    year_of_passing: Optional[int] = None
    percentage_or_cgpa: Optional[str] = None
    board_or_university: Optional[str] = None
    roll_number: Optional[str] = None
    is_current: bool = False
    state_of_institution: Optional[str] = None
    district_of_institution: Optional[str] = None


class EducationRecordOut(EducationRecordIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


# -- Profile -------------------------------------------------------------------
class ProfileUpdateRequest(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    caste: Optional[str] = None
    tribe_name: Optional[str] = None
    state_of_domicile: Optional[str] = None
    is_pvtg: Optional[bool] = None
    is_divyangjan: Optional[bool] = None
    annual_family_income: Optional[int] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    education_records: Optional[list[EducationRecordIn]] = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    caste: Optional[str] = None
    tribe_name: Optional[str] = None
    state_of_domicile: Optional[str] = None
    is_pvtg: bool
    is_divyangjan: bool
    annual_family_income: Optional[int] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    is_profile_complete: bool
    education_records: list[EducationRecordOut] = []
