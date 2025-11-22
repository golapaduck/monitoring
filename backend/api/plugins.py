"""플러그인 관리 API."""

from flask import Blueprint, jsonify, request, session
from plugins.loader import get_plugin_loader
from utils.database import save_plugin_config, get_plugin_config, get_program_plugins as db_get_program_plugins, delete_plugin_config

plugins_api = Blueprint('plugins_api', __name__, url_prefix='/api/plugins')


@plugins_api.route('/available', methods=['GET'])
def list_available_plugins():
    """사용 가능한 플러그인 목록 조회.
    
    Returns:
        JSON: {
            "plugins": [
                {
                    "id": "rcon",
                    "name": "RCON Controller",
                    "description": "...",
                    "config_schema": {...},
                    "actions": {...}
                },
                ...
            ]
        }
    """
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        loader = get_plugin_loader()
        plugins = loader.get_available_plugins()
        return jsonify({"plugins": plugins}), 200
    except Exception as e:
        print(f"[Plugins API] 플러그인 목록 조회 오류: {str(e)}")
        return jsonify({"error": str(e)}), 500


@plugins_api.route('/program/<int:program_id>', methods=['GET'])
def get_program_plugins(program_id):
    """프로그램의 플러그인 설정 조회.
    
    Args:
        program_id: 프로그램 ID
        
    Returns:
        JSON: {
            "plugins": [
                {
                    "plugin_id": "rcon",
                    "config": {...},
                    "enabled": true
                },
                ...
            ]
        }
    """
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        plugins = db_get_program_plugins(program_id)
        return jsonify({"plugins": plugins}), 200
    except Exception as e:
        print(f"[Plugins API] 프로그램 플러그인 조회 오류: {str(e)}")
        return jsonify({"error": str(e)}), 500


@plugins_api.route('/program/<int:program_id>/<plugin_id>', methods=['POST'])
def configure_plugin(program_id, plugin_id):
    """플러그인 설정 저장.
    
    Args:
        program_id: 프로그램 ID
        plugin_id: 플러그인 ID
        
    Request Body:
        {
            "config": {...},
            "enabled": true
        }
        
    Returns:
        JSON: {"success": true}
    """
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        data = request.get_json()
        config = data.get("config", {})
        enabled = data.get("enabled", True)
        
        # 플러그인 로더에서 검증
        loader = get_plugin_loader()
        if plugin_id not in loader.plugins:
            return jsonify({"error": "플러그인을 찾을 수 없습니다"}), 404
        
        # 임시 인스턴스로 설정 검증
        print(f"[Plugins API] 설정 검증 시작 - plugin_id: {plugin_id}, config: {config}")
        temp_instance = loader.plugins[plugin_id](program_id=program_id, config=config)
        valid, error = temp_instance.validate_config(config)
        print(f"[Plugins API] 설정 검증 결과 - valid: {valid}, error: {error}")
        if not valid:
            return jsonify({"error": f"설정 유효성 검사 실패: {error}"}), 400
        
        # 데이터베이스에 저장
        save_plugin_config(program_id, plugin_id, config, enabled)
        
        # 플러그인 로드 (활성화된 경우)
        if enabled:
            loader.load_plugin(program_id, plugin_id, config)
        else:
            loader.unload_plugin(program_id, plugin_id)
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"[Plugins API] 플러그인 설정 저장 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@plugins_api.route('/program/<int:program_id>/<plugin_id>', methods=['DELETE'])
def remove_plugin(program_id, plugin_id):
    """플러그인 제거.
    
    Args:
        program_id: 프로그램 ID
        plugin_id: 플러그인 ID
        
    Returns:
        JSON: {"success": true}
    """
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        # 플러그인 언로드
        loader = get_plugin_loader()
        loader.unload_plugin(program_id, plugin_id)
        
        # 데이터베이스에서 삭제
        delete_plugin_config(program_id, plugin_id)
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"[Plugins API] 플러그인 제거 오류: {str(e)}")
        return jsonify({"error": str(e)}), 500


@plugins_api.route('/program/<int:program_id>/<plugin_id>/action', methods=['POST'])
def execute_plugin_action(program_id, plugin_id):
    """플러그인 액션 실행.
    
    Args:
        program_id: 프로그램 ID
        plugin_id: 플러그인 ID
        
    Request Body:
        {
            "action": "send_command",
            "params": {...}
        }
        
    Returns:
        JSON: {
            "success": true,
            "message": "...",
            "data": {...}
        }
    """
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        action_name = data.get("action")
        params = data.get("params", {})
        
        if not action_name:
            return jsonify({"error": "액션 이름이 필요합니다"}), 400
        
        # 플러그인 인스턴스 조회
        loader = get_plugin_loader()
        plugin = loader.get_plugin_instance(program_id, plugin_id)
        
        if not plugin:
            return jsonify({"error": "플러그인이 로드되지 않았습니다"}), 404
        
        # 액션 실행
        result = plugin.execute_action(action_name, params)
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[Plugins API] 플러그인 액션 실행 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"액션 실행 실패: {str(e)}"
        }), 500
