"""플러그인 로더 및 관리자."""

import importlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Type
from .base import PluginBase


class PluginLoader:
    """플러그인을 동적으로 로드하고 관리하는 클래스."""
    
    def __init__(self):
        """플러그인 로더 초기화."""
        self.plugins: Dict[str, Type[PluginBase]] = {}  # plugin_id -> PluginClass
        self.instances: Dict[int, Dict[str, PluginBase]] = {}  # program_id -> {plugin_id -> instance}
        self.plugins_dir = Path(__file__).parent / "available"
        
    def discover_plugins(self) -> List[str]:
        """사용 가능한 플러그인 자동 발견.
        
        Returns:
            list: 발견된 플러그인 ID 목록
        """
        discovered = []
        
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return discovered
        
        # plugins/available/ 디렉토리에서 Python 파일 검색
        for file in self.plugins_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
                
            plugin_id = file.stem
            try:
                # 동적 import
                module_name = f"plugins.available.{plugin_id}"
                module = importlib.import_module(module_name)
                
                # PluginBase를 상속한 클래스 찾기
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, PluginBase) and 
                        attr is not PluginBase):
                        
                        self.plugins[plugin_id] = attr
                        discovered.append(plugin_id)
                        print(f"[Plugin Loader] 플러그인 발견: {plugin_id}")
                        break
                        
            except Exception as e:
                print(f"[Plugin Loader] 플러그인 로드 실패 ({plugin_id}): {str(e)}")
        
        return discovered
    
    def get_available_plugins(self) -> List[Dict[str, str]]:
        """사용 가능한 플러그인 목록 조회.
        
        Returns:
            list: 플러그인 정보 목록
        """
        result = []
        for plugin_id, plugin_class in self.plugins.items():
            # 임시 인스턴스 생성하여 메타데이터 조회
            temp_instance = plugin_class(program_id=0)
            result.append({
                "id": plugin_id,
                "name": temp_instance.get_name(),
                "description": temp_instance.get_description(),
                "config_schema": temp_instance.get_config_schema(),
                "actions": temp_instance.get_actions()
            })
        return result
    
    def load_plugin(self, program_id: int, plugin_id: str, config: Dict = None) -> Optional[PluginBase]:
        """특정 프로그램에 플러그인 로드.
        
        Args:
            program_id: 프로그램 ID
            plugin_id: 플러그인 ID
            config: 플러그인 설정
            
        Returns:
            PluginBase: 플러그인 인스턴스 또는 None
        """
        if plugin_id not in self.plugins:
            print(f"[Plugin Loader] 플러그인을 찾을 수 없음: {plugin_id}")
            return None
        
        try:
            plugin_class = self.plugins[plugin_id]
            instance = plugin_class(program_id=program_id, config=config)
            
            # 설정 유효성 검사
            valid, error = instance.validate_config(config or {})
            if not valid:
                print(f"[Plugin Loader] 설정 유효성 검사 실패: {error}")
                return None
            
            # 인스턴스 저장
            if program_id not in self.instances:
                self.instances[program_id] = {}
            self.instances[program_id][plugin_id] = instance
            
            print(f"[Plugin Loader] 플러그인 로드 성공: {plugin_id} (프로그램 {program_id})")
            return instance
            
        except Exception as e:
            print(f"[Plugin Loader] 플러그인 로드 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def unload_plugin(self, program_id: int, plugin_id: str) -> bool:
        """플러그인 언로드.
        
        Args:
            program_id: 프로그램 ID
            plugin_id: 플러그인 ID
            
        Returns:
            bool: 성공 여부
        """
        if program_id in self.instances and plugin_id in self.instances[program_id]:
            del self.instances[program_id][plugin_id]
            print(f"[Plugin Loader] 플러그인 언로드: {plugin_id} (프로그램 {program_id})")
            return True
        return False
    
    def get_plugin_instance(self, program_id: int, plugin_id: str) -> Optional[PluginBase]:
        """플러그인 인스턴스 조회.
        
        Args:
            program_id: 프로그램 ID
            plugin_id: 플러그인 ID
            
        Returns:
            PluginBase: 플러그인 인스턴스 또는 None
        """
        if program_id in self.instances:
            return self.instances[program_id].get(plugin_id)
        return None
    
    def get_program_plugins(self, program_id: int) -> Dict[str, PluginBase]:
        """특정 프로그램의 모든 플러그인 조회.
        
        Args:
            program_id: 프로그램 ID
            
        Returns:
            dict: plugin_id -> instance 매핑
        """
        return self.instances.get(program_id, {})
    
    def trigger_hook(self, program_id: int, hook_name: str, *args, **kwargs) -> None:
        """프로그램의 모든 플러그인에 훅 이벤트 전달.
        
        Args:
            program_id: 프로그램 ID
            hook_name: 훅 메서드 이름 (예: "on_program_start")
            *args, **kwargs: 훅 메서드에 전달할 인자
        """
        plugins = self.get_program_plugins(program_id)
        for plugin_id, plugin in plugins.items():
            try:
                hook_method = getattr(plugin, hook_name, None)
                if hook_method and callable(hook_method):
                    hook_method(*args, **kwargs)
            except Exception as e:
                print(f"[Plugin Loader] 훅 실행 오류 ({plugin_id}.{hook_name}): {str(e)}")


# 전역 플러그인 로더 인스턴스
_loader = None


def get_plugin_loader() -> PluginLoader:
    """전역 플러그인 로더 인스턴스 반환.
    
    Returns:
        PluginLoader: 플러그인 로더 인스턴스
    """
    global _loader
    if _loader is None:
        _loader = PluginLoader()
        _loader.discover_plugins()
    return _loader
