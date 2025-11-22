"""REST API Controller 플러그인.

HTTP 요청을 보내 외부 API를 호출하는 플러그인입니다.
프로그램 시작/종료 시 웹훅 전송, 헬스체크 등에 활용할 수 있습니다.
"""

import requests
import json
from typing import Dict, Any, Optional
from plugins.base import PluginBase


class RestApiPlugin(PluginBase):
    """REST API Controller 플러그인."""
    
    def __init__(self, program_id: int, config: Dict[str, Any] = None):
        """플러그인 초기화."""
        super().__init__(program_id, config)
    
    def get_name(self) -> str:
        return "REST API Controller"
    
    def get_description(self) -> str:
        return "HTTP 요청을 보내 외부 API를 호출합니다. 웹훅, 헬스체크, 데이터 조회 등에 활용할 수 있습니다."
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "title": "기본 URL",
                    "default": "http://localhost:8080",
                    "description": "API 서버의 기본 URL (예: http://api.example.com)"
                },
                "timeout": {
                    "type": "number",
                    "title": "타임아웃 (초)",
                    "default": 10.0,
                    "minimum": 1,
                    "maximum": 60,
                    "description": "요청 타임아웃"
                },
                "auth_type": {
                    "type": "string",
                    "title": "인증 방식",
                    "default": "none",
                    "enum": ["none", "bearer", "basic", "api_key"],
                    "description": "API 인증 방식"
                },
                "auth_token": {
                    "type": "string",
                    "title": "인증 토큰/키",
                    "default": "",
                    "description": "Bearer 토큰, API 키 등",
                    "format": "password"
                },
                "on_start_enabled": {
                    "type": "boolean",
                    "title": "시작 시 API 호출",
                    "default": False,
                    "description": "프로그램 시작 시 자동으로 API 호출"
                },
                "on_start_endpoint": {
                    "type": "string",
                    "title": "시작 시 엔드포인트",
                    "default": "/api/program/start",
                    "description": "프로그램 시작 시 호출할 엔드포인트"
                },
                "on_stop_enabled": {
                    "type": "boolean",
                    "title": "종료 시 API 호출",
                    "default": False,
                    "description": "프로그램 종료 시 자동으로 API 호출"
                },
                "on_stop_endpoint": {
                    "type": "string",
                    "title": "종료 시 엔드포인트",
                    "default": "/api/program/stop",
                    "description": "프로그램 종료 시 호출할 엔드포인트"
                }
            },
            "required": ["base_url"]
        }
    
    def get_actions(self) -> Dict[str, Dict[str, Any]]:
        return {
            "get_request": {
                "title": "GET 요청",
                "description": "GET 메서드로 API를 호출합니다",
                "params": {
                    "endpoint": {
                        "type": "string",
                        "title": "엔드포인트",
                        "description": "호출할 엔드포인트 (예: /api/status)"
                    },
                    "params": {
                        "type": "string",
                        "title": "쿼리 파라미터 (JSON)",
                        "description": "쿼리 파라미터 (JSON 형식, 선택사항)"
                    }
                }
            },
            "post_request": {
                "title": "POST 요청",
                "description": "POST 메서드로 API를 호출합니다",
                "params": {
                    "endpoint": {
                        "type": "string",
                        "title": "엔드포인트",
                        "description": "호출할 엔드포인트 (예: /api/data)"
                    },
                    "body": {
                        "type": "string",
                        "title": "요청 본문 (JSON)",
                        "description": "요청 본문 (JSON 형식)"
                    }
                }
            },
            "put_request": {
                "title": "PUT 요청",
                "description": "PUT 메서드로 API를 호출합니다",
                "params": {
                    "endpoint": {
                        "type": "string",
                        "title": "엔드포인트",
                        "description": "호출할 엔드포인트"
                    },
                    "body": {
                        "type": "string",
                        "title": "요청 본문 (JSON)",
                        "description": "요청 본문 (JSON 형식)"
                    }
                }
            },
            "delete_request": {
                "title": "DELETE 요청",
                "description": "DELETE 메서드로 API를 호출합니다",
                "params": {
                    "endpoint": {
                        "type": "string",
                        "title": "엔드포인트",
                        "description": "호출할 엔드포인트"
                    }
                }
            },
            "health_check": {
                "title": "헬스체크",
                "description": "서버 상태를 확인합니다",
                "params": {
                    "endpoint": {
                        "type": "string",
                        "title": "헬스체크 엔드포인트",
                        "description": "헬스체크 엔드포인트 (기본: /health)"
                    }
                }
            }
        }
    
    def execute_action(self, action_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """액션 실행."""
        params = params or {}
        
        if action_name == "get_request":
            endpoint = params.get("endpoint", "")
            if not endpoint:
                return {"success": False, "message": "엔드포인트가 필요합니다"}
            
            query_params = {}
            if params.get("params"):
                try:
                    query_params = json.loads(params.get("params"))
                except json.JSONDecodeError:
                    return {"success": False, "message": "쿼리 파라미터는 JSON 형식이어야 합니다"}
            
            return self._send_request("GET", endpoint, params=query_params)
        
        elif action_name == "post_request":
            endpoint = params.get("endpoint", "")
            if not endpoint:
                return {"success": False, "message": "엔드포인트가 필요합니다"}
            
            body = {}
            if params.get("body"):
                try:
                    body = json.loads(params.get("body"))
                except json.JSONDecodeError:
                    return {"success": False, "message": "요청 본문은 JSON 형식이어야 합니다"}
            
            return self._send_request("POST", endpoint, json=body)
        
        elif action_name == "put_request":
            endpoint = params.get("endpoint", "")
            if not endpoint:
                return {"success": False, "message": "엔드포인트가 필요합니다"}
            
            body = {}
            if params.get("body"):
                try:
                    body = json.loads(params.get("body"))
                except json.JSONDecodeError:
                    return {"success": False, "message": "요청 본문은 JSON 형식이어야 합니다"}
            
            return self._send_request("PUT", endpoint, json=body)
        
        elif action_name == "delete_request":
            endpoint = params.get("endpoint", "")
            if not endpoint:
                return {"success": False, "message": "엔드포인트가 필요합니다"}
            
            return self._send_request("DELETE", endpoint)
        
        elif action_name == "health_check":
            endpoint = params.get("endpoint", "/health")
            return self._send_request("GET", endpoint)
        
        return {
            "success": False,
            "message": f"알 수 없는 액션: {action_name}"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """설정 유효성 검사."""
        base_url = config.get("base_url", "").strip()
        if not base_url:
            return False, "기본 URL이 필요합니다"
        
        if not base_url.startswith(("http://", "https://")):
            return False, "URL은 http:// 또는 https://로 시작해야 합니다"
        
        timeout = config.get("timeout")
        if timeout is not None:
            try:
                timeout = float(timeout)
                if timeout < 1 or timeout > 60:
                    return False, "타임아웃은 1-60초 범위여야 합니다"
            except (ValueError, TypeError):
                return False, "타임아웃은 숫자여야 합니다"
        
        return True, None
    
    def on_program_start(self, pid: int) -> None:
        """프로그램 시작 시 호출."""
        print(f"[REST API Plugin] 프로그램 시작 (PID: {pid})")
        
        if self.config.get("on_start_enabled"):
            endpoint = self.config.get("on_start_endpoint", "/api/program/start")
            body = {
                "program_id": self.program_id,
                "pid": pid,
                "event": "start"
            }
            result = self._send_request("POST", endpoint, json=body)
            if result["success"]:
                print(f"[REST API Plugin] 시작 알림 전송 성공: {endpoint}")
            else:
                print(f"[REST API Plugin] 시작 알림 전송 실패: {result['message']}")
    
    def on_program_stop(self, pid: int) -> None:
        """프로그램 종료 시 호출."""
        print(f"[REST API Plugin] 프로그램 종료 (PID: {pid})")
        
        if self.config.get("on_stop_enabled"):
            endpoint = self.config.get("on_stop_endpoint", "/api/program/stop")
            body = {
                "program_id": self.program_id,
                "pid": pid,
                "event": "stop"
            }
            result = self._send_request("POST", endpoint, json=body)
            if result["success"]:
                print(f"[REST API Plugin] 종료 알림 전송 성공: {endpoint}")
            else:
                print(f"[REST API Plugin] 종료 알림 전송 실패: {result['message']}")
    
    def on_program_crash(self, pid: int) -> None:
        """프로그램 크래시 시 호출."""
        print(f"[REST API Plugin] 프로그램 크래시 감지 (PID: {pid})")
        
        if self.config.get("on_stop_enabled"):
            endpoint = self.config.get("on_stop_endpoint", "/api/program/stop")
            body = {
                "program_id": self.program_id,
                "pid": pid,
                "event": "crash"
            }
            result = self._send_request("POST", endpoint, json=body)
            if result["success"]:
                print(f"[REST API Plugin] 크래시 알림 전송 성공: {endpoint}")
            else:
                print(f"[REST API Plugin] 크래시 알림 전송 실패: {result['message']}")
    
    def _send_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """HTTP 요청 전송.
        
        Args:
            method: HTTP 메서드 (GET, POST, PUT, DELETE)
            endpoint: API 엔드포인트
            **kwargs: requests 라이브러리에 전달할 추가 인자
            
        Returns:
            dict: 실행 결과
        """
        try:
            base_url = self.config.get("base_url", "").rstrip("/")
            url = f"{base_url}{endpoint}"
            timeout = self.config.get("timeout", 10.0)
            
            # 헤더 설정
            headers = kwargs.pop("headers", {})
            auth_type = self.config.get("auth_type", "none")
            auth_token = self.config.get("auth_token", "")
            
            if auth_type == "bearer" and auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            elif auth_type == "api_key" and auth_token:
                headers["X-API-Key"] = auth_token
            
            # 요청 전송
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
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
                "data": {
                    "status_code": response.status_code,
                    "response": response_data,
                    "url": url
                }
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "요청 타임아웃"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "연결 실패"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"요청 실패: {str(e)}"
            }
