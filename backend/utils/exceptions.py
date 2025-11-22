"""커스텀 예외 클래스.

애플리케이션 전반에서 사용할 예외를 정의합니다.
"""


class MonitoringError(Exception):
    """모니터링 시스템 기본 예외.
    
    모든 커스텀 예외의 베이스 클래스.
    
    Attributes:
        message: 에러 메시지
        status_code: HTTP 상태 코드
        error_code: 에러 코드
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        error_code: str = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)
    
    def to_dict(self):
        """딕셔너리로 변환."""
        return {
            "success": False,
            "error": self.message,
            "error_code": self.error_code
        }


class ProcessNotFoundError(MonitoringError):
    """프로세스를 찾을 수 없음."""
    
    def __init__(self, process_name: str):
        super().__init__(
            f"프로세스를 찾을 수 없습니다: {process_name}",
            status_code=404,
            error_code="PROCESS_NOT_FOUND"
        )
        self.process_name = process_name


class ProcessStartError(MonitoringError):
    """프로세스 시작 실패."""
    
    def __init__(self, process_name: str, reason: str):
        super().__init__(
            f"프로세스 시작 실패: {process_name} - {reason}",
            status_code=500,
            error_code="PROCESS_START_ERROR"
        )
        self.process_name = process_name
        self.reason = reason


class ProcessStopError(MonitoringError):
    """프로세스 종료 실패."""
    
    def __init__(self, process_name: str, reason: str):
        super().__init__(
            f"프로세스 종료 실패: {process_name} - {reason}",
            status_code=500,
            error_code="PROCESS_STOP_ERROR"
        )
        self.process_name = process_name
        self.reason = reason


class ProgramNotFoundError(MonitoringError):
    """프로그램을 찾을 수 없음."""
    
    def __init__(self, program_id: int):
        super().__init__(
            f"프로그램을 찾을 수 없습니다: ID {program_id}",
            status_code=404,
            error_code="PROGRAM_NOT_FOUND"
        )
        self.program_id = program_id


class PluginNotFoundError(MonitoringError):
    """플러그인을 찾을 수 없음."""
    
    def __init__(self, plugin_id: str):
        super().__init__(
            f"플러그인을 찾을 수 없습니다: {plugin_id}",
            status_code=404,
            error_code="PLUGIN_NOT_FOUND"
        )
        self.plugin_id = plugin_id


class PluginLoadError(MonitoringError):
    """플러그인 로드 실패."""
    
    def __init__(self, plugin_id: str, reason: str):
        super().__init__(
            f"플러그인 로드 실패: {plugin_id} - {reason}",
            status_code=500,
            error_code="PLUGIN_LOAD_ERROR"
        )
        self.plugin_id = plugin_id
        self.reason = reason


class PluginExecutionError(MonitoringError):
    """플러그인 실행 실패."""
    
    def __init__(self, plugin_id: str, action: str, reason: str):
        super().__init__(
            f"플러그인 실행 실패: {plugin_id}.{action} - {reason}",
            status_code=500,
            error_code="PLUGIN_EXECUTION_ERROR"
        )
        self.plugin_id = plugin_id
        self.action = action
        self.reason = reason


class ValidationError(MonitoringError):
    """입력값 검증 실패."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            f"입력값 검증 실패: {field} - {message}",
            status_code=400,
            error_code="VALIDATION_ERROR"
        )
        self.field = field


class AuthenticationError(MonitoringError):
    """인증 실패."""
    
    def __init__(self, message: str = "인증이 필요합니다"):
        super().__init__(
            message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(MonitoringError):
    """권한 부족."""
    
    def __init__(self, message: str = "권한이 부족합니다"):
        super().__init__(
            message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )


class DatabaseError(MonitoringError):
    """데이터베이스 오류."""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            f"데이터베이스 오류: {operation} - {reason}",
            status_code=500,
            error_code="DATABASE_ERROR"
        )
        self.operation = operation
        self.reason = reason


class ConfigurationError(MonitoringError):
    """설정 오류."""
    
    def __init__(self, key: str, message: str):
        super().__init__(
            f"설정 오류: {key} - {message}",
            status_code=500,
            error_code="CONFIGURATION_ERROR"
        )
        self.key = key
