"""플러그인 베이스 클래스."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PluginBase(ABC):
    """모든 플러그인이 상속해야 하는 베이스 클래스.
    
    플러그인은 프로그램별 커스텀 기능을 제공합니다.
    예: RCON 명령어 실행, 서버 상태 조회, 자동 백업 등
    """
    
    def __init__(self, program_id: int, config: Dict[str, Any] = None):
        """플러그인 초기화.
        
        Args:
            program_id: 프로그램 ID
            config: 플러그인 설정 (JSON)
        """
        self.program_id = program_id
        self.config = config or {}
        self.enabled = True
    
    @abstractmethod
    def get_name(self) -> str:
        """플러그인 이름 반환.
        
        Returns:
            str: 플러그인 이름 (예: "RCON Controller")
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """플러그인 설명 반환.
        
        Returns:
            str: 플러그인 설명
        """
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """플러그인 설정 스키마 반환.
        
        프론트엔드에서 설정 폼을 자동 생성하는 데 사용됩니다.
        
        Returns:
            dict: JSON Schema 형식의 설정 스키마
            
        Example:
            {
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "title": "서버 주소",
                        "default": "localhost"
                    },
                    "port": {
                        "type": "integer",
                        "title": "포트",
                        "default": 25575
                    }
                },
                "required": ["host", "port"]
            }
        """
        pass
    
    @abstractmethod
    def get_actions(self) -> Dict[str, Dict[str, Any]]:
        """플러그인이 제공하는 액션 목록 반환.
        
        Returns:
            dict: 액션 이름을 키로 하는 딕셔너리
            
        Example:
            {
                "send_command": {
                    "title": "명령어 실행",
                    "description": "RCON 명령어를 실행합니다",
                    "params": {
                        "command": {
                            "type": "string",
                            "title": "명령어"
                        }
                    }
                }
            }
        """
        pass
    
    @abstractmethod
    def execute_action(self, action_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """액션 실행.
        
        Args:
            action_name: 실행할 액션 이름
            params: 액션 파라미터
            
        Returns:
            dict: 실행 결과
            {
                "success": True/False,
                "message": "결과 메시지",
                "data": {...}  # 추가 데이터 (선택)
            }
        """
        pass
    
    def on_program_start(self, pid: int) -> None:
        """프로그램 시작 시 호출되는 훅.
        
        Args:
            pid: 프로세스 ID
        """
        pass
    
    def on_program_stop(self, pid: int) -> None:
        """프로그램 종료 시 호출되는 훅.
        
        Args:
            pid: 프로세스 ID
        """
        pass
    
    def on_program_crash(self, pid: int) -> None:
        """프로그램 크래시 시 호출되는 훅.
        
        Args:
            pid: 프로세스 ID
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """플러그인 상태 조회.
        
        Returns:
            dict: 플러그인 상태 정보
        """
        return {
            "enabled": self.enabled,
            "config": self.config
        }
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """설정 유효성 검사.
        
        Args:
            config: 검증할 설정
            
        Returns:
            tuple: (유효 여부, 에러 메시지)
        """
        # 기본 구현: 항상 유효
        return True, None
