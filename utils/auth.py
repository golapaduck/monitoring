"""사용자 인증 및 비밀번호 관리 유틸리티."""

import bcrypt


def hash_password(password):
    """비밀번호를 bcrypt로 해싱.
    
    Args:
        password: 평문 비밀번호 (str)
        
    Returns:
        str: 해싱된 비밀번호 (UTF-8 디코딩된 문자열)
    """
    # 비밀번호를 바이트로 인코딩하고 해싱
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # 데이터베이스 저장을 위해 문자열로 디코딩
    return hashed.decode('utf-8')


def verify_password(password, hashed_password):
    """비밀번호 검증.
    
    Args:
        password: 입력된 평문 비밀번호 (str)
        hashed_password: 저장된 해시 비밀번호 (str)
        
    Returns:
        bool: 비밀번호가 일치하면 True, 아니면 False
    """
    try:
        # 문자열을 바이트로 인코딩
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # bcrypt로 검증
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"⚠️ [Auth] 비밀번호 검증 오류: {str(e)}")
        return False


def migrate_plain_passwords(users_data):
    """기존 평문 비밀번호를 해시로 마이그레이션.
    
    Args:
        users_data: 사용자 데이터 딕셔너리
        
    Returns:
        dict: 마이그레이션된 사용자 데이터
    """
    migrated = False
    
    for user in users_data.get("users", []):
        # 비밀번호가 해시되지 않은 경우 (bcrypt 해시는 $2b$로 시작)
        if not user["password"].startswith("$2b$"):
            print(f"🔄 [Auth] 사용자 '{user['username']}'의 비밀번호를 해싱 중...")
            user["password"] = hash_password(user["password"])
            migrated = True
    
    if migrated:
        print("✅ [Auth] 비밀번호 마이그레이션 완료")
    
    return users_data
