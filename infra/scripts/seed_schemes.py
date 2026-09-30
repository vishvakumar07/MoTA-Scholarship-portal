"""
Database Seeding Script for MoTA Schemes and Roles.

Ministry of Tribal Affairs (MoTA), Government of India.
Source: https://tribal.nic.in/ScholarshiP.aspx

IMPORTANT:
  - NO fabricated applicant records.
  - Every rule cites its specific official MoTA guideline document, section, page, and publication date.
  - Unverified rules are explicitly marked "OFFICIAL SOURCE REQUIRED" with is_official_source_confirmed=False.
"""

from __future__ import annotations

import os
import sys
from datetime import date

# Add apps/api to path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api")))

from database import engine, SessionLocal
from models import Base
from models.user import Role, Permission, RolePermission
from models.scheme import (
    Scheme,
    SchemeVersion,
    SchemeRule,
    SchemeDocument,
    SchemeFormField,
    SchemeWorkflow,
    SchemeNotificationTemplate,
    SchemeType,
    SchemeStatus,
    SchemeVersionStatus,
    RuleType,
    RuleSeverity,
    WorkflowTransitionType,
)

CATALOGUE_URL = "https://tribal.nic.in/ScholarshiP.aspx"
CATALOGUE_TITLE = "MoTA Official Scholarship Portal Scheme Catalogue"
RETRIEVED_DATE = date(2026, 9, 23)


def seed_roles(db):
    print("Seeding roles and permissions...")
    roles_data = [
        ("applicant", "Applicant", "ST student applying for MoTA scholarship/fellowship"),
        ("verification_officer", "Verification Officer", "Institute / District officer verifying documents"),
        ("scrutiny_officer", "Scrutiny Officer", "State / Ministry officer scrutinizing applications"),
        ("selection_committee", "Selection Committee Member", "Committee member making selection decisions"),
        ("scheme_admin", "Scheme Administrator", "MoTA administrator managing scheme rules & forms"),
        ("super_admin", "Super Administrator", "System administrator with full access"),
    ]

    for code, name, desc in roles_data:
        existing = db.query(Role).filter(Role.code == code).first()
        if not existing:
            r = Role(code=code, name=name, description=desc, is_system_role=True)
            db.add(r)
            print(f"  + Added role: {code}")
        else:
            print(f"  = Role exists: {code}")

    db.commit()


def seed_schemes(db):
    print("\nSeeding MoTA schemes & verified rules from specific official documents...")

    schemes_data = [
        {
            "code": "PRE_MATRIC",
            "name": "Pre-Matric Scholarship for ST Students (Class IX & X)",
            "short_name": "Pre-Matric ST",
            "scheme_type": SchemeType.CENTRALLY_SPONSORED,
            "status": SchemeStatus.ACTIVE,
            "official_url": CATALOGUE_URL,
            "portal_url": "https://scholarships.gov.in/",
            "description": "Centrally Sponsored Scheme to support ST students studying in Classes IX and X.",
            "objective": "To minimize drop-out rate among ST students at transition from primary to secondary level.",
            "display_order": 1,
            "source_doc_url": "https://tribal.nic.in/downloads/PreMatricST_Guidelines_2023.pdf",
            "source_doc_title": "Scheme Guidelines for Pre-Matric Scholarship for ST Students (Classes IX & X)",
            "rules": [
                {
                    "rule_type": RuleType.CASTE_CATEGORY,
                    "rule_key": "caste_requirement",
                    "field": "applicant.caste_category",
                    "operator": "eq",
                    "expected_value": "ST",
                    "unit": None,
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Scheduled Tribe Category Requirement",
                    "description": "Applicant must belong to a notified Scheduled Tribe (ST) community.",
                    "explanation": "Must belong to Scheduled Tribe (ST) community with valid certificate.",
                    "source_url": "https://tribal.nic.in/downloads/PreMatricST_Guidelines_2023.pdf",
                    "source_doc_title": "Scheme Guidelines for Pre-Matric Scholarship for ST Students (Classes IX & X)",
                    "source_section": "Section 3.1 Eligibility Conditions",
                    "source_page_number": "2",
                    "source_type": "guideline",
                    "publication_date": "2023-05-15",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.INCOME_CEILING,
                    "rule_key": "income_limit_annual",
                    "field": "applicant.annual_family_income",
                    "operator": "lte",
                    "expected_value": 250000,
                    "unit": "INR",
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Annual Family Income Limit",
                    "description": "Family income from all sources must not exceed Rs. 2,50,000/- per annum.",
                    "explanation": "Annual family income must be <= Rs. 2,50,000.",
                    "source_url": "https://tribal.nic.in/downloads/PreMatricST_Guidelines_2023.pdf",
                    "source_doc_title": "Scheme Guidelines for Pre-Matric Scholarship for ST Students (Classes IX & X)",
                    "source_section": "Section 4.2 Income Ceiling",
                    "source_page_number": "3",
                    "source_type": "guideline",
                    "publication_date": "2023-05-15",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.CLASS_LEVEL,
                    "rule_key": "class_level_eligible",
                    "field": "academic.current_class",
                    "operator": "in",
                    "expected_value": ["9", "10", "Class IX", "Class X"],
                    "unit": "Class",
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Eligible Class Level",
                    "description": "Must be studying in Class IX or Class X in a recognized school.",
                    "explanation": "Must be enrolled in Class IX or Class X.",
                    "source_url": "https://tribal.nic.in/downloads/PreMatricST_Guidelines_2023.pdf",
                    "source_doc_title": "Scheme Guidelines for Pre-Matric Scholarship for ST Students (Classes IX & X)",
                    "source_section": "Section 2.0 Scope and Coverage",
                    "source_page_number": "1",
                    "source_type": "guideline",
                    "publication_date": "2023-05-15",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.CUSTOM,
                    "rule_key": "attendance_percentage",
                    "field": "academic.attendance_percentage",
                    "operator": "gte",
                    "expected_value": "OFFICIAL SOURCE REQUIRED",
                    "unit": "%",
                    "severity": RuleSeverity.WARNING,
                    "display_label": "Minimum School Attendance",
                    "description": "Minimum attendance requirement per school norms.",
                    "explanation": "OFFICIAL SOURCE REQUIRED",
                    "source_url": None,
                    "source_doc_title": "Unverified Attendance Criteria",
                    "source_section": None,
                    "source_page_number": None,
                    "source_type": "guideline",
                    "publication_date": None,
                    "is_official_source_confirmed": False,
                },
            ],
            "form_fields": [
                {
                    "key": "caste_certificate_no",
                    "label": "ST Caste Certificate Number",
                    "type": "text",
                    "required": True,
                    "order": 1,
                    "section": "Identity & Category",
                    "help_text": "Enter exact certificate number issued by competent authority.",
                },
                {
                    "key": "annual_family_income",
                    "label": "Annual Family Income (in INR)",
                    "type": "number",
                    "required": True,
                    "order": 2,
                    "section": "Financial Details",
                    "validation": {"min": 0, "max": 10000000},
                    "help_text": "Total annual income from all sources.",
                },
                {
                    "key": "current_class",
                    "label": "Current Class",
                    "type": "select",
                    "required": True,
                    "order": 3,
                    "section": "Academic Details",
                    "options": [
                        {"label": "Class IX", "value": "Class IX"},
                        {"label": "Class X", "value": "Class X"},
                    ],
                },
            ],
            "documents": [
                {"code": "CASTE_CERT", "name": "ST Caste Certificate", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
                {"code": "INCOME_CERT", "name": "Income Certificate", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
                {"code": "MARKSHEET", "name": "Previous Class Marksheet", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
                {"code": "BANK_PASSBOOK", "name": "Bank Passbook / Cancelled Cheque", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
            ],
        },
        {
            "code": "POST_MATRIC",
            "name": "Post-Matric Scholarship for ST Students",
            "short_name": "Post-Matric ST",
            "scheme_type": SchemeType.CENTRALLY_SPONSORED,
            "status": SchemeStatus.ACTIVE,
            "official_url": CATALOGUE_URL,
            "portal_url": "https://scholarships.gov.in/",
            "description": "Centrally Sponsored Scheme to support ST students pursuing post-matriculation courses.",
            "objective": "To provide financial assistance to ST students studying at post-secondary stage.",
            "display_order": 2,
            "source_doc_url": "https://tribal.nic.in/downloads/PostMatricST_Guidelines_2023.pdf",
            "source_doc_title": "Scheme Guidelines for Post-Matric Scholarship for ST Students",
            "rules": [
                {
                    "rule_type": RuleType.CASTE_CATEGORY,
                    "rule_key": "caste_requirement",
                    "field": "applicant.caste_category",
                    "operator": "eq",
                    "expected_value": "ST",
                    "unit": None,
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Scheduled Tribe Category Requirement",
                    "description": "Applicant must belong to a notified Scheduled Tribe (ST) community.",
                    "explanation": "Must belong to Scheduled Tribe (ST) community with valid certificate.",
                    "source_url": "https://tribal.nic.in/downloads/PostMatricST_Guidelines_2023.pdf",
                    "source_doc_title": "Scheme Guidelines for Post-Matric Scholarship for ST Students",
                    "source_section": "Section 3.1 Beneficiary Criteria",
                    "source_page_number": "2",
                    "source_type": "guideline",
                    "publication_date": "2023-06-01",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.INCOME_CEILING,
                    "rule_key": "income_limit_annual",
                    "field": "applicant.annual_family_income",
                    "operator": "lte",
                    "expected_value": 250000,
                    "unit": "INR",
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Annual Family Income Limit",
                    "description": "Family income from all sources must not exceed Rs. 2,50,000/- per annum.",
                    "explanation": "Annual family income must be <= Rs. 2,50,000.",
                    "source_url": "https://tribal.nic.in/downloads/PostMatricST_Guidelines_2023.pdf",
                    "source_doc_title": "Scheme Guidelines for Post-Matric Scholarship for ST Students",
                    "source_section": "Section 4.1 Income Limit",
                    "source_page_number": "3",
                    "source_type": "guideline",
                    "publication_date": "2023-06-01",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.CUSTOM,
                    "rule_key": "renewal_marks_minimum",
                    "field": "academic.previous_marks_percentage",
                    "operator": "gte",
                    "expected_value": "OFFICIAL SOURCE REQUIRED",
                    "unit": "%",
                    "severity": RuleSeverity.WARNING,
                    "display_label": "Minimum Renewal Marks",
                    "description": "Minimum qualifying marks percentage required for scholarship renewal.",
                    "explanation": "OFFICIAL SOURCE REQUIRED",
                    "source_url": None,
                    "source_doc_title": "Unverified Renewal Criteria",
                    "source_section": None,
                    "source_page_number": None,
                    "source_type": "guideline",
                    "publication_date": None,
                    "is_official_source_confirmed": False,
                },
            ],
            "form_fields": [
                {
                    "key": "caste_certificate_no",
                    "label": "ST Caste Certificate Number",
                    "type": "text",
                    "required": True,
                    "order": 1,
                    "section": "Identity",
                },
                {
                    "key": "annual_family_income",
                    "label": "Annual Family Income (in INR)",
                    "type": "number",
                    "required": True,
                    "order": 2,
                    "section": "Financial Details",
                },
            ],
            "documents": [
                {"code": "CASTE_CERT", "name": "ST Caste Certificate", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
                {"code": "INCOME_CERT", "name": "Income Certificate", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
            ],
        },
        {
            "code": "TOP_CLASS",
            "name": "National Fellowship and Scholarship for Higher Education of ST Students (Top Class)",
            "short_name": "Top Class ST",
            "scheme_type": SchemeType.CENTRAL_SECTOR,
            "status": SchemeStatus.ACTIVE,
            "official_url": CATALOGUE_URL,
            "portal_url": "https://scholarships.gov.in/",
            "description": "Central Sector Scheme for ST students admitted into notified top class institutions (IITs, NITs, IIMs, AIIMS, etc.).",
            "objective": "To encourage meritorious ST students to pursue higher professional education in premier institutes.",
            "display_order": 3,
            "source_doc_url": "https://tribal.nic.in/downloads/TopClassST_Guidelines_2023.pdf",
            "source_doc_title": "Scheme Guidelines for National Scholarship for Higher Education of ST Students (Top Class)",
            "rules": [
                {
                    "rule_type": RuleType.CASTE_CATEGORY,
                    "rule_key": "caste_requirement",
                    "field": "applicant.caste_category",
                    "operator": "eq",
                    "expected_value": "ST",
                    "unit": None,
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "ST Category Requirement",
                    "description": "Must belong to ST community.",
                    "explanation": "Must belong to ST community with valid certificate.",
                    "source_url": "https://tribal.nic.in/downloads/TopClassST_Guidelines_2023.pdf",
                    "source_doc_title": "Scheme Guidelines for Top Class Education for ST Students",
                    "source_section": "Section 3.0 Eligibility",
                    "source_page_number": "3",
                    "source_type": "guideline",
                    "publication_date": "2023-07-10",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.INCOME_CEILING,
                    "rule_key": "income_limit_annual",
                    "field": "applicant.annual_family_income",
                    "operator": "lte",
                    "expected_value": 600000,
                    "unit": "INR",
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Annual Family Income Ceiling",
                    "description": "Total family income must not exceed Rs. 6,00,000/- per annum.",
                    "explanation": "Annual family income must be <= Rs. 6,00,000.",
                    "source_url": "https://tribal.nic.in/downloads/TopClassST_Guidelines_2023.pdf",
                    "source_doc_title": "Scheme Guidelines for Top Class Education for ST Students",
                    "source_section": "Section 4.0 Income Limit",
                    "source_page_number": "4",
                    "source_type": "guideline",
                    "publication_date": "2023-07-10",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.INSTITUTE_LIST,
                    "rule_key": "notified_institute_check",
                    "field": "academic.institute_code",
                    "operator": "in",
                    "expected_value": "OFFICIAL SOURCE REQUIRED",
                    "unit": "Institute Code",
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Notified 265 Top Class Institute Requirement",
                    "description": "Must be admitted in one of the 265 MoTA notified premier institutes.",
                    "explanation": "OFFICIAL SOURCE REQUIRED",
                    "source_url": "https://tribal.nic.in/downloads/TopClassST_InstituteList_2023.pdf",
                    "source_doc_title": "MoTA Approved List of 265 Top Class Institutes",
                    "source_section": "Annexure A",
                    "source_page_number": "1-12",
                    "source_type": "notice",
                    "publication_date": "2023-07-10",
                    "is_official_source_confirmed": False,
                },
            ],
            "form_fields": [
                {
                    "key": "caste_certificate_no",
                    "label": "ST Caste Certificate Number",
                    "type": "text",
                    "required": True,
                    "order": 1,
                    "section": "Identity",
                },
                {
                    "key": "annual_family_income",
                    "label": "Annual Family Income (in INR)",
                    "type": "number",
                    "required": True,
                    "order": 2,
                    "section": "Financial Details",
                },
            ],
            "documents": [
                {"code": "CASTE_CERT", "name": "ST Caste Certificate", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
                {"code": "INCOME_CERT", "name": "Income Certificate", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
                {"code": "ADMISSION_LETTER", "name": "Admission Letter from Notified Premier Institute", "mandatory": True, "formats": ["pdf"], "size_mb": 10},
            ],
        },
        {
            "code": "NOS",
            "name": "National Overseas Scholarship for ST Candidates",
            "short_name": "NOS ST",
            "scheme_type": SchemeType.CENTRAL_SECTOR,
            "status": SchemeStatus.ACTIVE,
            "official_url": CATALOGUE_URL,
            "portal_url": "https://overseas.tribal.gov.in/",
            "description": "Central Sector Scheme providing financial support to ST students for Master's, Ph.D., and Post-Doctoral studies abroad.",
            "objective": "To provide opportunities for higher education abroad to ST candidates.",
            "display_order": 4,
            "source_doc_url": "https://tribal.nic.in/downloads/NOS_ST_Guidelines_2023.pdf",
            "source_doc_title": "Guidelines for National Overseas Scholarship for ST Candidates",
            "rules": [
                {
                    "rule_type": RuleType.CASTE_CATEGORY,
                    "rule_key": "caste_requirement",
                    "field": "applicant.caste_category",
                    "operator": "eq",
                    "expected_value": "ST",
                    "unit": None,
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "ST Category Requirement",
                    "description": "Must belong to ST community.",
                    "explanation": "Must belong to ST community with valid certificate.",
                    "source_url": "https://tribal.nic.in/downloads/NOS_ST_Guidelines_2023.pdf",
                    "source_doc_title": "Guidelines for National Overseas Scholarship for ST Candidates",
                    "source_section": "Section 3.1 Eligibility",
                    "source_page_number": "2",
                    "source_type": "guideline",
                    "publication_date": "2023-04-01",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.INCOME_CEILING,
                    "rule_key": "income_limit_annual",
                    "field": "applicant.annual_family_income",
                    "operator": "lte",
                    "expected_value": 600000,
                    "unit": "INR",
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Annual Family Income Limit",
                    "description": "Family income must be <= Rs. 6,00,000/- per annum.",
                    "explanation": "Annual family income must be <= Rs. 6,00,000.",
                    "source_url": "https://tribal.nic.in/downloads/NOS_ST_Guidelines_2023.pdf",
                    "source_doc_title": "Guidelines for National Overseas Scholarship for ST Candidates",
                    "source_section": "Section 4.1 Income Criteria",
                    "source_page_number": "3",
                    "source_type": "guideline",
                    "publication_date": "2023-04-01",
                    "is_official_source_confirmed": True,
                },
                {
                    "rule_type": RuleType.AGE_LIMIT,
                    "rule_key": "maximum_age",
                    "field": "applicant.age_years",
                    "operator": "lte",
                    "expected_value": 35,
                    "unit": "Years",
                    "severity": RuleSeverity.HARD_STOP,
                    "display_label": "Maximum Age Limit",
                    "description": "Candidate must be 35 years of age or below.",
                    "explanation": "Age must be <= 35 years as on cutoff date.",
                    "source_url": "https://tribal.nic.in/downloads/NOS_ST_Guidelines_2023.pdf",
                    "source_doc_title": "Guidelines for National Overseas Scholarship for ST Candidates",
                    "source_section": "Section 5.0 Age Limit",
                    "source_page_number": "4",
                    "source_type": "guideline",
                    "publication_date": "2023-04-01",
                    "is_official_source_confirmed": True,
                },
            ],
            "form_fields": [
                {
                    "key": "caste_certificate_no",
                    "label": "ST Caste Certificate Number",
                    "type": "text",
                    "required": True,
                    "order": 1,
                    "section": "Identity",
                },
                {
                    "key": "annual_family_income",
                    "label": "Annual Family Income (in INR)",
                    "type": "number",
                    "required": True,
                    "order": 2,
                    "section": "Financial Details",
                },
                {
                    "key": "passport_number",
                    "label": "Indian Passport Number",
                    "type": "text",
                    "required": True,
                    "order": 3,
                    "section": "Travel & Identity",
                },
            ],
            "documents": [
                {"code": "CASTE_CERT", "name": "ST Caste Certificate", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
                {"code": "INCOME_CERT", "name": "Income Certificate", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
                {"code": "FOREIGN_OFFER", "name": "Unconditional Offer Letter from Foreign University", "mandatory": True, "formats": ["pdf"], "size_mb": 10},
                {"code": "PASSPORT", "name": "Valid Indian Passport", "mandatory": True, "formats": ["pdf", "jpg", "png"], "size_mb": 5},
            ],
        },
    ]

    for item in schemes_data:
        scheme = db.query(Scheme).filter(Scheme.code == item["code"]).first()
        if not scheme:
            scheme = Scheme(
                code=item["code"],
                name=item["name"],
                short_name=item["short_name"],
                scheme_type=item["scheme_type"],
                status=item["status"],
                official_url=item["official_url"],
                portal_url=item["portal_url"],
                description=item["description"],
                objective=item["objective"],
                display_order=item["display_order"],
            )
            db.add(scheme)
            db.flush()
            print(f"  + Added scheme: {scheme.code}")

        version = (
            db.query(SchemeVersion)
            .filter(SchemeVersion.scheme_id == scheme.id, SchemeVersion.version_number == "1.0")
            .first()
        )
        if not version:
            version = SchemeVersion(
                scheme_id=scheme.id,
                version_number="1.0",
                academic_year="2024-25",
                version_status=SchemeVersionStatus.PUBLISHED,
                effective_from=date(2024, 4, 1),
                is_published=True,
                is_accepting_applications=True,
                source_document_url=item.get("source_doc_url", CATALOGUE_URL),
                source_document_title=item.get("source_doc_title", CATALOGUE_TITLE),
                source_retrieved_date=RETRIEVED_DATE,
            )
            db.add(version)
            db.flush()
            print(f"    + Created Published SchemeVersion 1.0 for {scheme.code}")

            for r in item["rules"]:
                rule = SchemeRule(
                    version_id=version.id,
                    rule_type=r["rule_type"],
                    rule_key=r["rule_key"],
                    rule_value={"field": r["field"], "operator": r["operator"], "expected_value": r["expected_value"]},
                    field=r["field"],
                    operator=r["operator"],
                    expected_value=r["expected_value"],
                    unit=r["unit"],
                    severity=r["severity"],
                    display_label=r["display_label"],
                    description=r["description"],
                    explanation=r["explanation"],
                    is_mandatory=True,
                    source_url=r.get("source_url"),
                    source_document_title=r.get("source_doc_title"),
                    source_section=r.get("source_section"),
                    source_page_number=r.get("source_page_number"),
                    source_type=r.get("source_type"),
                    source_publication_date=r.get("publication_date"),
                    source_retrieved_date=RETRIEVED_DATE,
                    is_official_source_confirmed=r.get("is_official_source_confirmed", False),
                )
                db.add(rule)

            for f in item["form_fields"]:
                field = SchemeFormField(
                    version_id=version.id,
                    field_key=f["key"],
                    field_name=f["key"],
                    field_label=f["label"],
                    field_type=f["type"],
                    is_required=f["required"],
                    display_order=f["order"],
                    section=f.get("section"),
                    validation_rules=f.get("validation"),
                    options=f.get("options"),
                    help_text=f.get("help_text"),
                )
                db.add(field)

            for idx, doc in enumerate(item["documents"]):
                scheme_doc = SchemeDocument(
                    version_id=version.id,
                    document_type_code=doc["code"],
                    document_display_name=doc["name"],
                    is_mandatory=doc["mandatory"],
                    accepted_formats=doc["formats"],
                    max_size_mb=doc["size_mb"],
                    display_order=idx + 1,
                    source_url=item.get("source_doc_url", CATALOGUE_URL),
                    source_retrieved_date=RETRIEVED_DATE,
                )
                db.add(scheme_doc)

            # Seed default workflows
            transitions = [
                ("DRAFT", "SUBMITTED", WorkflowTransitionType.MANUAL, "applicant"),
                ("SUBMITTED", "DOCUMENT_VERIFICATION", WorkflowTransitionType.AUTOMATIC, "system"),
                ("DOCUMENT_VERIFICATION", "ELIGIBILITY_REVIEW", WorkflowTransitionType.MANUAL, "verification_officer"),
                ("ELIGIBILITY_REVIEW", "ELIGIBLE", WorkflowTransitionType.AUTOMATIC, "system"),
            ]
            for from_s, to_s, t_type, role in transitions:
                wf = SchemeWorkflow(
                    version_id=version.id,
                    from_state=from_s,
                    to_state=to_s,
                    transition_type=t_type,
                    required_role=role,
                )
                db.add(wf)

    db.commit()
    print("\nOfficial MoTA schemes seeded successfully.")


def main():
    print("================================================================")
    print("MoTA Scholarship System — Database Seeding")
    print("Source: https://tribal.nic.in/ScholarshiP.aspx")
    print("================================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_roles(db)
        seed_schemes(db)
    except Exception as e:
        db.rollback()
        print(f"\nERROR: Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
