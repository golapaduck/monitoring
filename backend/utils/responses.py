"""표준 API 응답 헬퍼.

일관된 API 응답 형식을 제공합니다.
"""

from flask import jsonify
from typing import Any, Optional, Dict, Tuple


def success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    status: int = 200
) -> Tuple[Any, int]:
    """성공 응답 생성.
    
    Args:
        data: 응답 데이터
        message: 성공 메시지
        status: HTTP 상태 코드 (기본: 200)
    
    Returns:
        (JSON 응답, 상태 코드)
    
    Example:
        return success_response({"users": users}, "조회 성공")
        # {"success": True, "message": "조회 성공", "data": {"users": [...]}}
    """
    response: Dict[str, Any] = {"success": True}
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), status


def error_response(
    message: str,
    status: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Tuple[Any, int]:
    """에러 응답 생성.
    
    Args:
        message: 에러 메시지
        status: HTTP 상태 코드 (기본: 400)
        error_code: 에러 코드 (선택)
        details: 추가 상세 정보 (선택)
    
    Returns:
        (JSON 응답, 상태 코드)
    
    Example:
        return error_response("프로그램을 찾을 수 없습니다", 404, "PROGRAM_NOT_FOUND")
        # {"success": False, "error": "...", "error_code": "PROGRAM_NOT_FOUND"}
    """
    response: Dict[str, Any] = {
        "success": False,
        "error": message
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return jsonify(response), status


def created_response(
    data: Optional[Any] = None,
    message: str = "생성되었습니다",
    resource_id: Optional[Any] = None
) -> Tuple[Any, int]:
    """리소스 생성 성공 응답 (201 Created).
    
    Args:
        data: 생성된 리소스 데이터
        message: 성공 메시지
        resource_id: 생성된 리소스 ID
    
    Returns:
        (JSON 응답, 201)
    
    Example:
        return created_response(program_data, "프로그램이 등록되었습니다", program_id)
    """
    response: Dict[str, Any] = {
        "success": True,
        "message": message
    }
    
    if resource_id is not None:
        response["id"] = resource_id
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), 201


def no_content_response() -> Tuple[str, int]:
    """내용 없음 응답 (204 No Content).
    
    리소스 삭제 성공 등에 사용.
    
    Returns:
        (빈 응답, 204)
    """
    return "", 204


def validation_error_response(
    errors: Dict[str, str],
    message: str = "입력값 검증 실패"
) -> Tuple[Any, int]:
    """입력값 검증 실패 응답 (400 Bad Request).
    
    Args:
        errors: 필드별 에러 메시지 {"field": "error message"}
        message: 전체 에러 메시지
    
    Returns:
        (JSON 응답, 400)
    
    Example:
        return validation_error_response({
            "name": "이름은 필수입니다",
            "path": "경로가 유효하지 않습니다"
        })
    """
    return error_response(
        message=message,
        status=400,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": errors}
    )
