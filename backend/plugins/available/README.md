# 플러그인 개발 가이드

이 디렉토리에 플러그인 파일을 추가하면 자동으로 로드됩니다.

## 플러그인 구조

```python
from plugins.base import PluginBase
from typing import Dict, Any

class MyPlugin(PluginBase):
    """플러그인 설명."""
    
    def get_name(self) -> str:
        return "My Plugin"
    
    def get_description(self) -> str:
        return "플러그인 설명"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "setting1": {
                    "type": "string",
                    "title": "설정 1",
                    "default": "기본값"
                }
            },
            "required": ["setting1"]
        }
    
    def get_actions(self) -> Dict[str, Dict[str, Any]]:
        return {
            "my_action": {
                "title": "내 액션",
                "description": "액션 설명",
                "params": {
                    "param1": {
                        "type": "string",
                        "title": "파라미터 1"
                    }
                }
            }
        }
    
    def execute_action(self, action_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if action_name == "my_action":
            # 액션 실행 로직
            return {
                "success": True,
                "message": "액션 실행 성공",
                "data": {}
            }
        
        return {
            "success": False,
            "message": f"알 수 없는 액션: {action_name}"
        }
    
    def on_program_start(self, pid: int) -> None:
        # 프로그램 시작 시 실행
        pass
    
    def on_program_stop(self, pid: int) -> None:
        # 프로그램 종료 시 실행
        pass
    
    def on_program_crash(self, pid: int) -> None:
        # 프로그램 크래시 시 실행
        pass
```

## 파일명 규칙

- 파일명은 플러그인 ID로 사용됩니다 (예: `rcon.py` -> ID: `rcon`)
- `_`로 시작하는 파일은 무시됩니다

## 다음 단계

Phase 2-5에서 RCON 플러그인을 예제로 구현할 예정입니다.
