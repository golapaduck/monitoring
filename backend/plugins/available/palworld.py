"""Palworld REST API 플러그인.

Palworld 서버를 REST API로 제어하는 플러그인입니다.
공식 Palworld REST API를 사용합니다.
"""

import requests
import json
from typing import Dict, Any, Optional, Tuple
from plugins.base import PluginBase


class PalworldPlugin(PluginBase):
    """Palworld REST API 플러그인."""
    
    def __init__(self, program_id: int, config: Dict[str, Any] = None):
        """플러그인 초기화."""
        super().__init__(program_id, config)
        self.base_url = None
        self.password = None
        
        if config:
            host = config.get("host", "localhost")
            port = config.get("port", 8212)
            self.base_url = f"http://{host}:{port}/v1/api"
            self.password = config.get("password", "")
            print(f"[Palworld Plugin] 초기화 - host: {host}, port: {port}, password 길이: {len(self.password)}")
    
    def get_name(self) -> str:
        return "Palworld REST API"
    
    def get_description(self) -> str:
        return "Palworld 서버를 REST API로 제어합니다. 서버 정보 조회, 플레이어 관리, 공지사항 전송 등을 지원합니다."
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "title": "서버 주소",
                    "default": "localhost",
                    "description": "Palworld 서버 주소"
                },
                "port": {
                    "type": "integer",
                    "title": "REST API 포트",
                    "default": 8212,
                    "minimum": 1,
                    "maximum": 65535,
                    "description": "REST API 포트 (기본: 8212)"
                },
                "password": {
                    "type": "string",
                    "title": "Admin 비밀번호",
                    "default": "",
                    "description": "PalWorldSettings.ini의 AdminPassword 값",
                    "format": "password"
                }
            },
            "required": ["password"]
        }
    
    def get_actions(self) -> Dict[str, Dict[str, Any]]:
        return {
            "get_info": {
                "title": "서버 정보 조회",
                "description": "서버 버전, 이름, 설명, World GUID를 조회합니다",
                "params": {}
            },
            "get_players": {
                "title": "플레이어 목록 조회",
                "description": "현재 접속 중인 플레이어 목록을 조회합니다",
                "params": {}
            },
            "get_settings": {
                "title": "서버 설정 조회",
                "description": "서버 설정을 조회합니다",
                "params": {}
            },
            "get_metrics": {
                "title": "서버 메트릭 조회",
                "description": "서버 성능 메트릭을 조회합니다",
                "params": {}
            },
            "announce": {
                "title": "공지사항 전송",
                "description": "모든 플레이어에게 공지사항을 전송합니다",
                "params": {
                    "message": {
                        "type": "string",
                        "title": "메시지",
                        "description": "전송할 공지사항"
                    }
                }
            },
            "kick_player": {
                "title": "플레이어 강퇴",
                "description": "특정 플레이어를 서버에서 강퇴합니다",
                "params": {
                    "userid": {
                        "type": "string",
                        "title": "사용자 ID",
                        "description": "강퇴할 플레이어의 Steam ID"
                    },
                    "message": {
                        "type": "string",
                        "title": "메시지",
                        "description": "강퇴 사유 (선택사항)"
                    }
                }
            },
            "ban_player": {
                "title": "플레이어 차단",
                "description": "특정 플레이어를 서버에서 차단합니다",
                "params": {
                    "userid": {
                        "type": "string",
                        "title": "사용자 ID",
                        "description": "차단할 플레이어의 Steam ID"
                    },
                    "message": {
                        "type": "string",
                        "title": "메시지",
                        "description": "차단 사유 (선택사항)"
                    }
                }
            },
            "unban_player": {
                "title": "플레이어 차단 해제",
                "description": "차단된 플레이어의 차단을 해제합니다",
                "params": {
                    "userid": {
                        "type": "string",
                        "title": "사용자 ID",
                        "description": "차단 해제할 플레이어의 Steam ID"
                    }
                }
            },
            "save_world": {
                "title": "월드 저장",
                "description": "현재 월드 상태를 저장합니다",
                "params": {}
            },
            "shutdown_server": {
                "title": "서버 종료",
                "description": "서버를 정상적으로 종료합니다",
                "params": {
                    "waittime": {
                        "type": "string",
                        "title": "대기 시간 (초)",
                        "description": "종료 전 대기 시간 (선택사항, 기본: 60)"
                    },
                    "message": {
                        "type": "string",
                        "title": "메시지",
                        "description": "종료 전 공지사항 (선택사항)"
                    }
                }
            },
            "force_stop_server": {
                "title": "서버 강제 종료",
                "description": "서버를 즉시 강제 종료합니다 (데이터 손실 가능)",
                "params": {}
            }
        }
    
    def execute_action(self, action_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """액션 실행."""
        params = params or {}
        
        if action_name == "get_info":
            return self._api_request("GET", "/info")
        
        elif action_name == "get_players":
            return self._api_request("GET", "/players")
        
        elif action_name == "get_settings":
            return self._api_request("GET", "/settings")
        
        elif action_name == "get_metrics":
            return self._api_request("GET", "/metrics")
        
        elif action_name == "announce":
            message = params.get("message", "")
            if not message:
                return {"success": False, "message": "메시지가 필요합니다"}
            return self._api_request("POST", "/announce", json={"message": message})
        
        elif action_name == "kick_player":
            userid = params.get("userid", "")
            if not userid:
                return {"success": False, "message": "사용자 ID가 필요합니다"}
            
            # Palworld REST API는 userid 필드 사용 (Steam ID: steam_xxx)
            body = {"userid": userid}
            if params.get("message"):
                body["message"] = params.get("message")
            
            print(f"[Palworld Plugin] kick_player body: {body}")
            return self._api_request("POST", "/kick", json=body)
        
        elif action_name == "ban_player":
            userid = params.get("userid", "")
            if not userid:
                return {"success": False, "message": "사용자 ID가 필요합니다"}
            
            # Palworld REST API는 userid 필드 사용 (Steam ID: steam_xxx)
            body = {"userid": userid}
            if params.get("message"):
                body["message"] = params.get("message")
            
            print(f"[Palworld Plugin] ban_player body: {body}")
            return self._api_request("POST", "/ban", json=body)
        
        elif action_name == "unban_player":
            userid = params.get("userid", "")
            if not userid:
                return {"success": False, "message": "사용자 ID가 필요합니다"}
            
            # Palworld REST API는 userid 필드 사용 (Steam ID: steam_xxx)
            body = {"userid": userid}
            print(f"[Palworld Plugin] unban_player body: {body}")
            return self._api_request("POST", "/unban", json=body)
        
        elif action_name == "save_world":
            return self._api_request("POST", "/save")
        
        elif action_name == "shutdown_server":
            # shutdown API는 waittime과 message가 required
            waittime = params.get("waittime", 60)  # 기본 60초
            try:
                waittime = int(waittime)
            except (ValueError, TypeError):
                waittime = 60
            
            message = params.get("message", "서버가 곧 종료됩니다")
            
            body = {
                "waittime": waittime,
                "message": message
            }
            
            return self._api_request("POST", "/shutdown", json=body)
        
        elif action_name == "force_stop_server":
            return self._api_request("POST", "/stop")
        
        return {
            "success": False,
            "message": f"알 수 없는 액션: {action_name}"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """설정 유효성 검사."""
        # host: default 값 적용
        host = config.get("host", "localhost").strip()
        if not host:
            return False, "서버 주소가 필요합니다"
        
        # port: default 값 적용
        port = config.get("port", 8212)
        if port is None or port == "":
            port = 8212
        
        try:
            port = int(port)
            if port < 1 or port > 65535:
                return False, "포트는 1-65535 범위여야 합니다"
        except (ValueError, TypeError):
            return False, "포트는 숫자여야 합니다"
        
        # password는 필수
        password = config.get("password", "").strip()
        if not password:
            return False, "Admin 비밀번호가 필요합니다"
        
        return True, None
    
    def on_program_start(self, pid: int) -> None:
        """프로그램 시작 시 호출."""
        print(f"[Palworld Plugin] 프로그램 시작 (PID: {pid})")
    
    def on_program_stop(self, pid: int) -> None:
        """프로그램 종료 시 호출."""
        print(f"[Palworld Plugin] 프로그램 종료 (PID: {pid})")
    
    def on_program_crash(self, pid: int) -> None:
        """프로그램 크래시 시 호출."""
        print(f"[Palworld Plugin] 프로그램 크래시 감지 (PID: {pid})")
    
    def _api_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Palworld REST API 요청.
        
        Args:
            method: HTTP 메서드 (GET, POST)
            endpoint: API 엔드포인트
            **kwargs: requests 라이브러리에 전달할 추가 인자
            
        Returns:
            dict: 실행 결과
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "message": "플러그인이 초기화되지 않았습니다"
                }
            
            url = f"{self.base_url}{endpoint}"
            # Palworld REST API는 Basic Auth 사용: username은 "admin", password는 AdminPassword
            auth = ("admin", self.password) if self.password else None
            
            # 명시적으로 헤더 설정
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            print(f"[Palworld Plugin] API 요청: {method} {url}")
            print(f"[Palworld Plugin] Password 존재: {bool(self.password)}, 길이: {len(self.password) if self.password else 0}")
            print(f"[Palworld Plugin] Auth: {('admin', '***') if auth else None}")
            print(f"[Palworld Plugin] Headers: {headers}")
            
            response = requests.request(
                method=method,
                url=url,
                auth=auth,
                headers=headers,
                timeout=10,
                **kwargs
            )
            
            # 응답 처리
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            return {
                "success": response.ok,
                "message": f"HTTP {response.status_code}",
                "data": response_data
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "요청 타임아웃"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "연결 실패 - 서버가 실행 중인지 확인하세요"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"요청 실패: {str(e)}"
            }
