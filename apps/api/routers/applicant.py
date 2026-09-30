"""
Applicant Profile router  -  /api/v1/applicant/*

GET  /api/v1/applicant/profile         -  Get or create applicant profile
PUT  /api/v1/applicant/profile         -  Update applicant profile
"""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.applicant import ApplicantProfile, ApplicantEducation, EducationLevel, Gender
from schemas.applicant import ProfileUpdateRequest, ProfileOut, EducationRecordOut
from security.rbac import get_current_user
from models.user import User

router = APIRouter(prefix="/applicant", tags=["Applicant Portal"])


def _get_or_create_profile(db: Session, user_id: uuid.UUID) -> ApplicantProfile:
    profile = (
        db.query(ApplicantProfile)
        .options(joinedload(ApplicantProfile.education_records))
        .filter(ApplicantProfile.user_id == user_id)
        .first()
    )
    if not profile:
        profile = ApplicantProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _profile_to_out(profile: ApplicantProfile) -> ProfileOut:
    edu = profile.education_records or []
    return ProfileOut(
        id=str(profile.id),
        user_id=str(profile.user_id),
        date_of_birth=profile.date_of_birth,
        gender=profile.gender.value if profile.gender else None,
        father_name=profile.father_name,
        mother_name=profile.mother_name,
        guardian_name=profile.guardian_name,
        caste=profile.caste,
        tribe_name=profile.tribe_name,
        state_of_domicile=profile.state_of_domicile,
        is_pvtg=profile.is_pvtg,
        is_divyangjan=profile.is_divyangjan,
        annual_family_income=profile.annual_family_income,
        address_line1=profile.address_line1,
        address_line2=profile.address_line2,
        city=profile.city,
        district=profile.district,
        state=profile.state,
        pincode=profile.pincode,
        is_profile_complete=profile.is_profile_complete,
        education_records=[
            EducationRecordOut(
                id=str(e.id),
                education_level=e.education_level.value,
                institution_name=e.institution_name,
                institution_code=e.institution_code,
                course_name=e.course_name,
                year_of_passing=e.year_of_passing,
                percentage_or_cgpa=e.percentage_or_cgpa,
                board_or_university=e.board_or_university,
                roll_number=e.roll_number,
                is_current=e.is_current,
                state_of_institution=e.state_of_institution,
                district_of_institution=e.district_of_institution,
            )
            for e in edu
        ],
    )


@router.get(
    "/profile",
    response_model=ProfileOut,
    summary="Get applicant profile (creates if not exists)",
)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the applicant''s extended profile. Creates an empty one on first call."""
    profile = _get_or_create_profile(db, current_user.id)
    # Reload with education
    profile = (
        db.query(ApplicantProfile)
        .options(joinedload(ApplicantProfile.education_records))
        .filter(ApplicantProfile.id == profile.id)
        .first()
    )
    return _profile_to_out(profile)


@router.put(
    "/profile",
    response_model=ProfileOut,
    summary="Update applicant profile",
)
def update_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the authenticated applicant''s profile fields."""
    profile = _get_or_create_profile(db, current_user.id)

    # Update scalar fields
    simple_fields = [
        "date_of_birth", "father_name", "mother_name", "guardian_name",
        "caste", "tribe_name", "state_of_domicile", "is_pvtg", "is_divyangjan",
        "annual_family_income", "address_line1", "address_line2",
        "city", "district", "state", "pincode",
    ]
    for field in simple_fields:
        val = getattr(body, field)
        if val is not None:
            setattr(profile, field, val)

    if body.gender is not None:
        try:
            profile.gender = Gender(body.gender)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid gender value: {body.gender}",
            )

    # Replace education records if provided
    if body.education_records is not None:
        db.query(ApplicantEducation).filter(
            ApplicantEducation.applicant_profile_id == profile.id
        ).delete(synchronize_session="fetch")

        for edu_in in body.education_records:
            try:
                level = EducationLevel(edu_in.education_level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid education_level: {edu_in.education_level}",
                )
            edu = ApplicantEducation(
                applicant_profile_id=profile.id,
                education_level=level,
                institution_name=edu_in.institution_name,
                institution_code=edu_in.institution_code,
                course_name=edu_in.course_name,
                year_of_passing=edu_in.year_of_passing,
                percentage_or_cgpa=edu_in.percentage_or_cgpa,
                board_or_university=edu_in.board_or_university,
                roll_number=edu_in.roll_number,
                is_current=edu_in.is_current,
                state_of_institution=edu_in.state_of_institution,
                district_of_institution=edu_in.district_of_institution,
            )
            db.add(edu)

    # Determine profile completeness
    required = [
        profile.date_of_birth, profile.gender, profile.caste,
        profile.state_of_domicile, profile.annual_family_income,
        profile.address_line1, profile.state, profile.pincode,
    ]
    profile.is_profile_complete = all(f is not None for f in required)

    db.commit()
    db.refresh(profile)

    # Reload with education
    profile = (
        db.query(ApplicantProfile)
        .options(joinedload(ApplicantProfile.education_records))
        .filter(ApplicantProfile.id == profile.id)
        .first()
    )
    return _profile_to_out(profile)
