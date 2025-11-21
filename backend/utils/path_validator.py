"""파일 경로 유효성 검증 유틸리티."""

import os
from pathlib import Path


def validate_program_path(path):
    """프로그램 경로의 유효성을 검증.
    
    Args:
        path: 검증할 파일 경로 (str)
        
    Returns:
        tuple: (유효 여부, 오류 메시지 또는 None)
    """
    if not path or not isinstance(path, str):
        return False, "경로가 제공되지 않았습니다."
    
    path = path.strip()
    
    if not path:
        return False, "경로가 비어있습니다."
    
    try:
        # Path 객체로 변환
        file_path = Path(path)
        
        # 절대 경로로 변환
        abs_path = file_path.resolve()
        
        # 파일 존재 여부 확인
        if not abs_path.exists():
            return False, f"파일이 존재하지 않습니다: {abs_path}"
        
        # 디렉토리가 아닌 파일인지 확인
        if not abs_path.is_file():
            return False, f"디렉토리입니다. 실행 파일을 선택해주세요: {abs_path}"
        
        # 실행 가능한 파일인지 확인 (확장자 체크)
        valid_extensions = ['.exe', '.bat', '.cmd', '.ps1', '.jar', '.py']
        if abs_path.suffix.lower() not in valid_extensions:
            return False, f"실행 가능한 파일이 아닙니다. 지원 형식: {', '.join(valid_extensions)}"
        
        # 읽기 권한 확인
        if not os.access(abs_path, os.R_OK):
            return False, f"파일에 대한 읽기 권한이 없습니다: {abs_path}"
        
        return True, None
        
    except Exception as e:
        return False, f"경로 검증 중 오류 발생: {str(e)}"


def normalize_path(path):
    """경로를 정규화 (절대 경로로 변환).
    
    Args:
        path: 정규화할 경로 (str)
        
    Returns:
        str: 정규화된 절대 경로
    """
    try:
        return str(Path(path).resolve())
    except Exception:
        return path


def get_path_info(path):
    """경로에 대한 상세 정보 조회.
    
    Args:
        path: 조회할 파일 경로 (str)
        
    Returns:
        dict: 파일 정보 또는 None
    """
    try:
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            return None
        
        stat_info = file_path.stat()
        
        return {
            "name": file_path.name,
            "path": str(file_path),
            "size": stat_info.st_size,
            "size_mb": round(stat_info.st_size / (1024 * 1024), 2),
            "extension": file_path.suffix,
            "parent": str(file_path.parent),
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "exists": True
        }
    except Exception as e:
        print(f"⚠️ [Path Validator] 경로 정보 조회 실패: {str(e)}")
        return None
