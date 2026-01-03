"""Privacy endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.privacy import (
    detect_pii,
    mask_value,
    mask_dataframe,
    k_anonymize,
    PIIType,
)

router = APIRouter()


class PIIDetectRequest(BaseModel):
    """Request to detect PII in data."""
    data: list[dict[str, Any]]
    fields: list[str] | None = None


class PIIDetectResponse(BaseModel):
    """PII detection result."""
    pii_found: bool
    detections: dict[str, list[dict[str, Any]]]
    summary: dict[str, int]


class MaskRequest(BaseModel):
    """Request to mask data."""
    data: list[dict[str, Any]]
    fields_to_mask: dict[str, str] | None = None
    auto_detect: bool = True


class AnonymizeRequest(BaseModel):
    """Request to anonymize data."""
    data: list[dict[str, Any]]
    quasi_identifiers: list[str]
    k: int = 5


@router.post("/privacy/detect", response_model=PIIDetectResponse)
async def detect_pii_endpoint(request: PIIDetectRequest):
    """
    Detect PII in data.

    Scans the provided data for personally identifiable information
    and returns the locations and types found.
    """
    from core.privacy import detect_pii_in_dataframe

    detections = detect_pii_in_dataframe(request.data, request.fields)

    # Build summary
    summary: dict[str, int] = {}
    for field, matches in detections.items():
        for match in matches:
            pii_type = match.pii_type.value
            summary[pii_type] = summary.get(pii_type, 0) + 1

    return PIIDetectResponse(
        pii_found=bool(detections),
        detections={
            field: [m.model_dump() for m in matches]
            for field, matches in detections.items()
        },
        summary=summary,
    )


@router.post("/privacy/mask")
async def mask_data_endpoint(request: MaskRequest):
    """
    Mask PII in data.

    Replaces PII with masked values while preserving data structure.
    """
    # Convert field names to PIIType if provided
    fields_to_mask = None
    if request.fields_to_mask:
        fields_to_mask = {}
        for field, pii_type_str in request.fields_to_mask.items():
            try:
                fields_to_mask[field] = PIIType(pii_type_str)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid PII type: {pii_type_str}",
                )

    masked = mask_dataframe(
        request.data,
        fields_to_mask=fields_to_mask,
        auto_detect=request.auto_detect,
    )

    return {
        "masked_data": masked,
        "records_processed": len(masked),
    }


@router.post("/privacy/anonymize")
async def anonymize_data_endpoint(request: AnonymizeRequest):
    """
    Anonymize data using k-anonymity.

    Generalizes quasi-identifiers to ensure each record is
    indistinguishable from at least k-1 other records.
    """
    if request.k < 2:
        raise HTTPException(
            status_code=400,
            detail="k must be at least 2 for k-anonymity",
        )

    anonymized = k_anonymize(
        request.data,
        quasi_identifiers=request.quasi_identifiers,
        k=request.k,
    )

    # Calculate information loss
    from core.privacy.anonymizer import calculate_information_loss
    info_loss = calculate_information_loss(
        request.data,
        anonymized,
        request.quasi_identifiers,
    )

    return {
        "anonymized_data": anonymized,
        "k": request.k,
        "records": len(anonymized),
        "information_loss": round(info_loss, 4),
    }


@router.get("/privacy/pii-types")
async def list_pii_types():
    """List all supported PII types."""
    return {
        "pii_types": [
            {
                "type": pii_type.value,
                "name": pii_type.name,
                "description": _get_pii_description(pii_type),
            }
            for pii_type in PIIType
        ]
    }


def _get_pii_description(pii_type: PIIType) -> str:
    """Get description for PII type."""
    descriptions = {
        PIIType.SSN: "주민등록번호 (Korean Social Security Number)",
        PIIType.PHONE_KR: "한국 전화번호",
        PIIType.PHONE: "전화번호",
        PIIType.EMAIL: "이메일 주소",
        PIIType.NAME: "이름/성명",
        PIIType.ADDRESS: "주소",
        PIIType.BIRTH_DATE: "생년월일",
        PIIType.CARD_NUMBER: "카드번호",
        PIIType.BANK_ACCOUNT: "계좌번호",
        PIIType.EMPLOYEE_ID: "사원번호",
    }
    return descriptions.get(pii_type, "")
