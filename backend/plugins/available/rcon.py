"""RCON (Remote Console) 플러그인.

게임 서버(Minecraft, Palworld 등)에 RCON 명령어를 전송하는 플러그인입니다.
"""

import socket
import struct
import time
from typing import Dict, Any, Optional
from plugins.base import PluginBase


class RCONClient:
    """RCON 프로토콜 클라이언트.
    
    Source RCON Protocol 구현
    https://developer.valvesoftware.com/wiki/Source_RCON_Protocol
    """
    
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0
    
    def __init__(self, host: str, port: int, password: str, timeout: float = 5.0):
        """RCON 클라이언트 초기화.
        
        Args:
            host: 서버 주소
            port: RCON 포트
            password: RCON 비밀번호
            timeout: 타임아웃 (초)
        """
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.request_id = 0
    
    def connect(self) -> bool:
        """서버에 연결 및 인증.
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            
            # 인증
            self.request_id += 1
            auth_packet = self._build_packet(self.request_id, self.SERVERDATA_AUTH, self.password)
            self.socket.send(auth_packet)
            
            # 인증 응답 수신
            response = self._receive_packet()
            if response is None or response[0] == -1:
                return False
            
            return True
            
        except Exception as e:
            print(f"[RCON] 연결 실패: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """연결 종료."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def send_command(self, command: str) -> Optional[str]:
        """명령어 전송 및 응답 수신.
        
        Args:
            command: 실행할 명령어
            
        Returns:
            str: 서버 응답 또는 None
        """
        if not self.socket:
            if not self.connect():
                return None
        
        try:
            self.request_id += 1
            command_packet = self._build_packet(self.request_id, self.SERVERDATA_EXECCOMMAND, command)
            self.socket.send(command_packet)
            
            # 응답 수신
            response = self._receive_packet()
            if response:
                return response[2]  # body
            return None
            
        except Exception as e:
            print(f"[RCON] 명령어 전송 실패: {str(e)}")
            self.disconnect()
            return None
    
    def _build_packet(self, request_id: int, packet_type: int, body: str) -> bytes:
        """RCON 패킷 생성.
        
        Args:
            request_id: 요청 ID
            packet_type: 패킷 타입
            body: 패킷 본문
            
        Returns:
            bytes: 패킷 데이터
        """
        body_bytes = body.encode('utf-8') + b'\x00\x00'
        size = len(body_bytes) + 10
        return struct.pack('<iii', size - 4, request_id, packet_type) + body_bytes
    
    def _receive_packet(self) -> Optional[tuple]:
        """RCON 패킷 수신.
        
        Returns:
            tuple: (request_id, packet_type, body) 또는 None
        """
        try:
            # 패킷 크기 수신 (4 bytes)
            size_data = self.socket.recv(4)
            if len(size_data) < 4:
                return None
            
            size = struct.unpack('<i', size_data)[0]
            
            # 나머지 패킷 수신
            data = b''
            while len(data) < size:
                chunk = self.socket.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
            
            # 패킷 파싱
            request_id, packet_type = struct.unpack('<ii', data[:8])
            body = data[8:-2].decode('utf-8', errors='ignore')
            
            return (request_id, packet_type, body)
            
        except Exception as e:
            print(f"[RCON] 패킷 수신 실패: {str(e)}")
            return None


class RCONPlugin(PluginBase):
    """RCON 플러그인."""
    
    def __init__(self, program_id: int, config: Dict[str, Any] = None):
        """플러그인 초기화."""
        super().__init__(program_id, config)
        self.client: Optional[RCONClient] = None
    
    def get_name(self) -> str:
        return "RCON Controller"
    
    def get_description(self) -> str:
        return "게임 서버에 RCON 명령어를 전송합니다. Minecraft, Palworld 등을 지원합니다."
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "title": "서버 주소",
                    "default": "localhost",
                    "description": "RCON 서버 주소"
                },
                "port": {
                    "type": "integer",
                    "title": "RCON 포트",
                    "default": 25575,
                    "minimum": 1,
                    "maximum": 65535,
                    "description": "RCON 포트 번호"
                },
                "password": {
                    "type": "string",
                    "title": "RCON 비밀번호",
                    "description": "서버 설정에서 지정한 RCON 비밀번호",
                    "format": "password"
                },
                "timeout": {
                    "type": "number",
                    "title": "타임아웃 (초)",
                    "default": 5.0,
                    "minimum": 1,
                    "maximum": 30,
                    "description": "명령어 실행 타임아웃"
                }
            },
            "required": ["host", "port", "password"]
        }
    
    def get_actions(self) -> Dict[str, Dict[str, Any]]:
        return {
            "send_command": {
                "title": "명령어 실행",
                "description": "RCON 명령어를 서버에 전송합니다",
                "params": {
                    "command": {
                        "type": "string",
                        "title": "명령어",
                        "description": "실행할 명령어 (예: 'save', 'broadcast Hello')"
                    }
                }
            },
            "test_connection": {
                "title": "연결 테스트",
                "description": "RCON 서버 연결을 테스트합니다",
                "params": {}
            },
            "get_server_info": {
                "title": "서버 정보 조회",
                "description": "서버 정보를 조회합니다 (info 명령어)",
                "params": {}
            },
            "save_world": {
                "title": "월드 저장",
                "description": "게임 월드를 저장합니다 (save 명령어)",
                "params": {}
            },
            "broadcast_message": {
                "title": "공지 전송",
                "description": "서버에 공지 메시지를 전송합니다",
                "params": {
                    "message": {
                        "type": "string",
                        "title": "메시지",
                        "description": "전송할 공지 메시지"
                    }
                }
            }
        }
    
    def execute_action(self, action_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """액션 실행."""
        params = params or {}
        
        if action_name == "send_command":
            command = params.get("command", "")
            if not command:
                return {
                    "success": False,
                    "message": "명령어가 필요합니다"
                }
            
            response = self._send_rcon_command(command)
            if response is not None:
                return {
                    "success": True,
                    "message": "명령어 실행 성공",
                    "data": {"response": response}
                }
            else:
                return {
                    "success": False,
                    "message": "명령어 실행 실패"
                }
        
        elif action_name == "test_connection":
            client = self._get_client()
            if client.connect():
                client.disconnect()
                return {
                    "success": True,
                    "message": "연결 성공"
                }
            else:
                return {
                    "success": False,
                    "message": "연결 실패"
                }
        
        elif action_name == "get_server_info":
            response = self._send_rcon_command("info")
            if response is not None:
                return {
                    "success": True,
                    "message": "서버 정보 조회 성공",
                    "data": {"info": response}
                }
            else:
                return {
                    "success": False,
                    "message": "서버 정보 조회 실패"
                }
        
        elif action_name == "save_world":
            response = self._send_rcon_command("save")
            if response is not None:
                return {
                    "success": True,
                    "message": "월드 저장 완료",
                    "data": {"response": response}
                }
            else:
                return {
                    "success": False,
                    "message": "월드 저장 실패"
                }
        
        elif action_name == "broadcast_message":
            message = params.get("message", "")
            if not message:
                return {
                    "success": False,
                    "message": "메시지가 필요합니다"
                }
            
            response = self._send_rcon_command(f"broadcast {message}")
            if response is not None:
                return {
                    "success": True,
                    "message": "공지 전송 완료",
                    "data": {"response": response}
                }
            else:
                return {
                    "success": False,
                    "message": "공지 전송 실패"
                }
        
        return {
            "success": False,
            "message": f"알 수 없는 액션: {action_name}"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """설정 유효성 검사."""
        host = config.get("host", "").strip()
        if not host:
            return False, "서버 주소가 필요합니다"
        
        # port: default 값 적용 (25575)
        port = config.get("port", 25575)
        if port is None or port == "":
            port = 25575
        
        # 포트를 정수로 변환 시도
        try:
            port = int(port)
            if port < 1 or port > 65535:
                return False, "포트는 1-65535 범위여야 합니다"
        except (ValueError, TypeError):
            return False, "포트는 숫자여야 합니다"
        
        password = config.get("password", "").strip()
        if not password:
            return False, "비밀번호가 필요합니다"
        
        return True, None
    
    def on_program_start(self, pid: int) -> None:
        """프로그램 시작 시 호출."""
        print(f"[RCON Plugin] 프로그램 시작 (PID: {pid})")
    
    def on_program_stop(self, pid: int) -> None:
        """프로그램 종료 시 호출."""
        print(f"[RCON Plugin] 프로그램 종료 (PID: {pid})")
        if self.client:
            self.client.disconnect()
    
    def on_program_crash(self, pid: int) -> None:
        """프로그램 크래시 시 호출."""
        print(f"[RCON Plugin] 프로그램 크래시 감지 (PID: {pid})")
        if self.client:
            self.client.disconnect()
    
    def _get_client(self) -> RCONClient:
        """RCON 클라이언트 인스턴스 반환."""
        if not self.client:
            self.client = RCONClient(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 25575),
                password=self.config.get("password", ""),
                timeout=self.config.get("timeout", 5.0)
            )
        return self.client
    
    def _send_rcon_command(self, command: str) -> Optional[str]:
        """RCON 명령어 전송.
        
        Args:
            command: 실행할 명령어
            
        Returns:
            str: 서버 응답 또는 None
        """
        client = self._get_client()
        response = client.send_command(command)
        return response
