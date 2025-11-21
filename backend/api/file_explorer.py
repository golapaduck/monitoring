"""파일 탐색기 API 엔드포인트."""

from flask import Blueprint, request, session, jsonify
from pathlib import Path
import os

# Blueprint 생성
file_explorer_api = Blueprint('file_explorer_api', __name__, url_prefix='/api/explorer')


@file_explorer_api.route("/list", methods=["POST"])
def list_directory():
    """디렉토리 내용 조회 API (관리자만).
    
    POST 요청으로 경로를 받아 해당 디렉토리의 파일 및 폴더 목록을 반환합니다.
    """
    try:
        if "user" not in session or session.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        
        data = request.get_json()
    except Exception as e:
        print(f"[File Explorer] JSON 파싱 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"요청 파싱 실패: {str(e)}"}), 400
    
    path = data.get("path", "")
    
    # 경로가 없으면 드라이브 목록 반환 (Windows)
    if not path:
        try:
            drives = []
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append({
                        "name": drive,
                        "path": drive,
                        "type": "drive",
                        "is_file": False,
                        "is_dir": True
                    })
            return jsonify({
                "path": "",
                "items": drives,
                "parent": None
            })
        except Exception as e:
            return jsonify({"error": f"드라이브 목록 조회 실패: {str(e)}"}), 500
    
    try:
        dir_path = Path(path)
        
        # 경로 존재 여부 확인
        if not dir_path.exists():
            return jsonify({"error": "경로가 존재하지 않습니다."}), 404
        
        # 디렉토리인지 확인
        if not dir_path.is_dir():
            return jsonify({"error": "디렉토리가 아닙니다."}), 400
        
        items = []
        
        # 디렉토리 내용 읽기
        try:
            for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    # 숨김 파일/폴더 건너뛰기 (선택사항)
                    if item.name.startswith('.'):
                        continue
                    
                    item_info = {
                        "name": item.name,
                        "path": str(item),
                        "is_file": item.is_file(),
                        "is_dir": item.is_dir()
                    }
                    
                    # 파일인 경우 추가 정보
                    if item.is_file():
                        stat_info = item.stat()
                        item_info["type"] = "file"
                        item_info["size"] = stat_info.st_size
                        item_info["extension"] = item.suffix.lower()
                        
                        # 실행 가능한 파일인지 확인
                        executable_extensions = ['.exe', '.bat', '.cmd', '.ps1', '.jar', '.py']
                        item_info["executable"] = item.suffix.lower() in executable_extensions
                    else:
                        item_info["type"] = "directory"
                    
                    items.append(item_info)
                    
                except (PermissionError, OSError):
                    # 접근 권한이 없는 항목은 건너뛰기
                    continue
        
        except PermissionError:
            return jsonify({"error": "디렉토리에 대한 접근 권한이 없습니다."}), 403
        
        # 부모 디렉토리 경로
        parent_path = str(dir_path.parent) if dir_path.parent != dir_path else None
        
        return jsonify({
            "path": str(dir_path),
            "items": items,
            "parent": parent_path,
            "total": len(items)
        })
        
    except Exception as e:
        return jsonify({"error": f"디렉토리 조회 실패: {str(e)}"}), 500


@file_explorer_api.route("/search", methods=["POST"])
def search_files():
    """파일 검색 API (관리자만).
    
    특정 디렉토리에서 파일명으로 검색합니다.
    """
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json()
    search_path = data.get("path", "C:\\")
    query = data.get("query", "").lower()
    max_results = data.get("max_results", 50)
    
    if not query:
        return jsonify({"error": "검색어가 필요합니다."}), 400
    
    try:
        dir_path = Path(search_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return jsonify({"error": "유효하지 않은 경로입니다."}), 400
        
        results = []
        count = 0
        
        # 재귀적으로 파일 검색 (최대 깊이 제한)
        def search_recursive(path, depth=0, max_depth=3):
            nonlocal count
            
            if count >= max_results or depth > max_depth:
                return
            
            try:
                for item in path.iterdir():
                    if count >= max_results:
                        break
                    
                    try:
                        # 파일명에 검색어 포함 여부 확인
                        if query in item.name.lower():
                            item_info = {
                                "name": item.name,
                                "path": str(item),
                                "is_file": item.is_file(),
                                "is_dir": item.is_dir(),
                                "type": "file" if item.is_file() else "directory"
                            }
                            
                            if item.is_file():
                                item_info["extension"] = item.suffix.lower()
                                executable_extensions = ['.exe', '.bat', '.cmd', '.ps1', '.jar', '.py']
                                item_info["executable"] = item.suffix.lower() in executable_extensions
                            
                            results.append(item_info)
                            count += 1
                        
                        # 디렉토리면 재귀 검색
                        if item.is_dir() and not item.name.startswith('.'):
                            search_recursive(item, depth + 1, max_depth)
                            
                    except (PermissionError, OSError):
                        continue
                        
            except (PermissionError, OSError):
                pass
        
        search_recursive(dir_path)
        
        return jsonify({
            "query": query,
            "path": str(dir_path),
            "results": results,
            "total": len(results),
            "truncated": count >= max_results
        })
        
    except Exception as e:
        return jsonify({"error": f"검색 실패: {str(e)}"}), 500


@file_explorer_api.route("/common-paths", methods=["GET"])
def get_common_paths():
    """자주 사용하는 경로 목록 반환 (관리자만)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    common_paths = []
    
    # 사용자 홈 디렉토리
    home = Path.home()
    if home.exists():
        common_paths.append({
            "name": "내 문서",
            "path": str(home / "Documents"),
            "icon": "📄"
        })
        common_paths.append({
            "name": "다운로드",
            "path": str(home / "Downloads"),
            "icon": "⬇️"
        })
        common_paths.append({
            "name": "바탕화면",
            "path": str(home / "Desktop"),
            "icon": "🖥️"
        })
    
    # Program Files
    program_files = Path("C:\\Program Files")
    if program_files.exists():
        common_paths.append({
            "name": "Program Files",
            "path": str(program_files),
            "icon": "📁"
        })
    
    program_files_x86 = Path("C:\\Program Files (x86)")
    if program_files_x86.exists():
        common_paths.append({
            "name": "Program Files (x86)",
            "path": str(program_files_x86),
            "icon": "📁"
        })
    
    # 시스템 드라이브
    common_paths.append({
        "name": "C 드라이브",
        "path": "C:\\",
        "icon": "💾"
    })
    
    return jsonify({
        "paths": common_paths
    })
