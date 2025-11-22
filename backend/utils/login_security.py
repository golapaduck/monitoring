"""로그인 보안 강화 모듈."""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import threading

# 환경 변수에서 설정 로드
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_ATTEMPT_WINDOW = int(os.getenv("LOGIN_ATTEMPT_WINDOW", "300"))  # 5분
LOGIN_LOCKOUT_DURATION = int(os.getenv("LOGIN_LOCKOUT_DURATION", "900"))  # 15분


class LoginSecurityManager:
    """로그인 보안 관리자.
    
    기능:
    - 로그인 시도 횟수 제한
    - 계정 잠금
    - 세션 고정 공격 방지
    """
    
    def __init__(self):
        """로그인 보안 관리자 초기화."""
        # 로그인 시도 기록: {username: [(timestamp, success), ...]}
        self.login_attempts: Dict[str, list] = {}
        
        # 계정 잠금 정보: {username: lockout_until_timestamp}
        self.locked_accounts: Dict[str, float] = {}
        
        # 스레드 안전성을 위한 락
        self.lock = threading.Lock()
    
    def is_account_locked(self, username: str) -> Tuple[bool, Optional[int]]:
        """계정 잠금 상태 확인.
        
        Args:
            username: 사용자명
        
        Returns:
            Tuple[bool, Optional[int]]: (잠금 여부, 남은 시간(초))
        """
        with self.lock:
            if username not in self.locked_accounts:
                return False, None
            
            lockout_until = self.locked_accounts[username]
            current_time = time.time()
            
            if current_time < lockout_until:
                remaining = int(lockout_until - current_time)
                return True, remaining
            else:
                # 잠금 시간 만료
                del self.locked_accounts[username]
                return False, None
    
    def record_login_attempt(self, username: str, success: bool) -> None:
        """로그인 시도 기록.
        
        Args:
            username: 사용자명
            success: 로그인 성공 여부
        """
        with self.lock:
            current_time = time.time()
            
            # 사용자 시도 기록 초기화
            if username not in self.login_attempts:
                self.login_attempts[username] = []
            
            # 새 시도 추가
            self.login_attempts[username].append((current_time, success))
            
            # 오래된 시도 기록 정리 (시간 창 밖)
            cutoff_time = current_time - LOGIN_ATTEMPT_WINDOW
            self.login_attempts[username] = [
                (ts, succ) for ts, succ in self.login_attempts[username]
                if ts > cutoff_time
            ]
            
            # 성공 시 시도 기록 초기화
            if success:
                self.login_attempts[username] = []
                if username in self.locked_accounts:
                    del self.locked_accounts[username]
    
    def check_and_lock_if_needed(self, username: str) -> Tuple[bool, int]:
        """로그인 실패 횟수 확인 및 필요 시 계정 잠금.
        
        Args:
            username: 사용자명
        
        Returns:
            Tuple[bool, int]: (잠금 여부, 실패 횟수)
        """
        with self.lock:
            if username not in self.login_attempts:
                return False, 0
            
            # 최근 실패 횟수 계산
            current_time = time.time()
            cutoff_time = current_time - LOGIN_ATTEMPT_WINDOW
            
            recent_failures = [
                (ts, succ) for ts, succ in self.login_attempts[username]
                if ts > cutoff_time and not succ
            ]
            
            failure_count = len(recent_failures)
            
            # 최대 시도 횟수 초과 시 계정 잠금
            if failure_count >= MAX_LOGIN_ATTEMPTS:
                lockout_until = current_time + LOGIN_LOCKOUT_DURATION
                self.locked_accounts[username] = lockout_until
                return True, failure_count
            
            return False, failure_count
    
    def get_remaining_attempts(self, username: str) -> int:
        """남은 로그인 시도 횟수 조회.
        
        Args:
            username: 사용자명
        
        Returns:
            int: 남은 시도 횟수
        """
        with self.lock:
            if username not in self.login_attempts:
                return MAX_LOGIN_ATTEMPTS
            
            # 최근 실패 횟수 계산
            current_time = time.time()
            cutoff_time = current_time - LOGIN_ATTEMPT_WINDOW
            
            recent_failures = [
                (ts, succ) for ts, succ in self.login_attempts[username]
                if ts > cutoff_time and not succ
            ]
            
            failure_count = len(recent_failures)
            remaining = MAX_LOGIN_ATTEMPTS - failure_count
            
            return max(0, remaining)
    
    def unlock_account(self, username: str) -> bool:
        """계정 잠금 해제 (관리자용).
        
        Args:
            username: 사용자명
        
        Returns:
            bool: 해제 성공 여부
        """
        with self.lock:
            if username in self.locked_accounts:
                del self.locked_accounts[username]
                self.login_attempts[username] = []
                return True
            return False
    
    def get_locked_accounts(self) -> Dict[str, int]:
        """잠긴 계정 목록 조회.
        
        Returns:
            Dict[str, int]: {username: remaining_seconds}
        """
        with self.lock:
            current_time = time.time()
            locked = {}
            
            for username, lockout_until in list(self.locked_accounts.items()):
                if current_time < lockout_until:
                    remaining = int(lockout_until - current_time)
                    locked[username] = remaining
                else:
                    # 만료된 잠금 제거
                    del self.locked_accounts[username]
            
            return locked
    
    def cleanup_old_attempts(self) -> int:
        """오래된 로그인 시도 기록 정리.
        
        Returns:
            int: 정리된 사용자 수
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - LOGIN_ATTEMPT_WINDOW * 2  # 2배 시간 후 정리
            
            cleaned = 0
            for username in list(self.login_attempts.keys()):
                self.login_attempts[username] = [
                    (ts, succ) for ts, succ in self.login_attempts[username]
                    if ts > cutoff_time
                ]
                
                # 빈 기록 삭제
                if not self.login_attempts[username]:
                    del self.login_attempts[username]
                    cleaned += 1
            
            return cleaned


# 전역 인스턴스
_login_security_manager = None


def get_login_security_manager() -> LoginSecurityManager:
    """로그인 보안 관리자 인스턴스 반환.
    
    Returns:
        LoginSecurityManager: 로그인 보안 관리자
    """
    global _login_security_manager
    if _login_security_manager is None:
        _login_security_manager = LoginSecurityManager()
    return _login_security_manager


def prevent_session_fixation(session) -> None:
    """세션 고정 공격 방지.
    
    로그인 성공 시 세션 ID를 재생성합니다.
    
    Args:
        session: Flask session 객체
    """
    # 기존 세션 데이터 백업
    session_data = dict(session)
    
    # 세션 초기화 (새 세션 ID 생성)
    session.clear()
    
    # 세션 데이터 복원
    session.update(session_data)
    
    # 세션 수정 플래그 설정
    session.modified = True
