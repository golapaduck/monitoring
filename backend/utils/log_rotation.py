"""로그 로테이션 시스템.

로그 파일을 자동으로 관리하고 오래된 로그를 정리합니다.
"""

import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class LogRotation:
    """로그 파일 로테이션 관리 클래스."""
    
    def __init__(self, log_dir="logs", max_bytes=10*1024*1024, backup_count=5, 
                 retention_days=30, check_interval=3600):
        """
        Args:
            log_dir: 로그 디렉토리 경로
            max_bytes: 로그 파일 최대 크기 (기본: 10MB)
            backup_count: 유지할 백업 파일 수 (기본: 5개)
            retention_days: 로그 보관 기간 (일 단위, 기본: 30일)
            check_interval: 로테이션 체크 간격 (초, 기본: 1시간)
        """
        self.log_dir = Path(log_dir)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.retention_days = retention_days
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        
        # 로그 디렉토리 생성
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def start(self):
        """로그 로테이션 시작."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._rotation_loop, daemon=True, name="LogRotation")
        self.thread.start()
        print(f"🔄 [Log Rotation] 로그 로테이션 시작 (간격: {self.check_interval}초)")
        
    def stop(self):
        """로그 로테이션 중지."""
        if not self.running:
            return
            
        self.running = False
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=2)
            except Exception:
                pass
        print("🛑 [Log Rotation] 로그 로테이션 중지")
        
    def _rotation_loop(self):
        """로테이션 루프 (백그라운드 스레드)."""
        while self.running:
            try:
                self._check_and_rotate()
                self._cleanup_old_logs()
            except Exception as e:
                print(f"⚠️ [Log Rotation] 로테이션 오류: {str(e)}")
            
            # 다음 체크까지 대기
            time.sleep(self.check_interval)
            
    def _check_and_rotate(self):
        """로그 파일 크기 확인 및 로테이션."""
        for log_file in self.log_dir.glob("*.log"):
            try:
                # 파일 크기 확인
                if log_file.stat().st_size >= self.max_bytes:
                    self._rotate_file(log_file)
            except Exception as e:
                print(f"⚠️ [Log Rotation] 파일 확인 오류 ({log_file.name}): {str(e)}")
                
    def _rotate_file(self, log_file):
        """로그 파일 로테이션 수행.
        
        Args:
            log_file: 로테이션할 로그 파일 경로
        """
        try:
            base_name = log_file.stem  # 확장자 제외한 파일명
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 백업 파일명: app_20231122_143025.log.gz
            backup_name = f"{base_name}_{timestamp}.log.gz"
            backup_path = self.log_dir / backup_name
            
            # 로그 파일을 gzip으로 압축하여 백업
            with open(log_file, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 원본 로그 파일 비우기
            with open(log_file, 'w') as f:
                f.write(f"# 로그 로테이션: {datetime.now().isoformat()}\n")
            
            print(f"🔄 [Log Rotation] 로테이션 완료: {log_file.name} -> {backup_name}")
            
            # 오래된 백업 파일 정리
            self._cleanup_backups(base_name)
            
        except Exception as e:
            print(f"⚠️ [Log Rotation] 로테이션 실패 ({log_file.name}): {str(e)}")
            
    def _cleanup_backups(self, base_name):
        """오래된 백업 파일 정리 (backup_count 초과 시).
        
        Args:
            base_name: 로그 파일 기본 이름
        """
        try:
            # 해당 로그의 모든 백업 파일 찾기
            backup_files = sorted(
                self.log_dir.glob(f"{base_name}_*.log.gz"),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # 최신 파일부터
            )
            
            # backup_count를 초과하는 파일 삭제
            if len(backup_files) > self.backup_count:
                for old_file in backup_files[self.backup_count:]:
                    old_file.unlink()
                    print(f"🗑️ [Log Rotation] 오래된 백업 삭제: {old_file.name}")
                    
        except Exception as e:
            print(f"⚠️ [Log Rotation] 백업 정리 오류: {str(e)}")
            
    def _cleanup_old_logs(self):
        """보관 기간이 지난 로그 파일 삭제."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for log_file in self.log_dir.glob("*.log.gz"):
                try:
                    # 파일 수정 시간 확인
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        log_file.unlink()
                        print(f"🗑️ [Log Rotation] 오래된 로그 삭제: {log_file.name} (생성: {file_mtime.date()})")
                        
                except Exception as e:
                    print(f"⚠️ [Log Rotation] 파일 삭제 오류 ({log_file.name}): {str(e)}")
                    
        except Exception as e:
            print(f"⚠️ [Log Rotation] 오래된 로그 정리 오류: {str(e)}")
            
    def rotate_now(self, log_file_name):
        """즉시 로테이션 수행 (수동 트리거).
        
        Args:
            log_file_name: 로테이션할 로그 파일 이름
        """
        log_file = self.log_dir / log_file_name
        if log_file.exists():
            self._rotate_file(log_file)
        else:
            print(f"⚠️ [Log Rotation] 파일 없음: {log_file_name}")
            
    def get_log_stats(self):
        """로그 파일 통계 정보 반환.
        
        Returns:
            dict: 로그 파일 통계 정보
        """
        try:
            stats = {
                "log_files": [],
                "backup_files": [],
                "total_size": 0
            }
            
            # 현재 로그 파일
            for log_file in self.log_dir.glob("*.log"):
                size = log_file.stat().st_size
                stats["log_files"].append({
                    "name": log_file.name,
                    "size": size,
                    "size_mb": round(size / 1024 / 1024, 2),
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
                stats["total_size"] += size
                
            # 백업 파일
            for backup_file in self.log_dir.glob("*.log.gz"):
                size = backup_file.stat().st_size
                stats["backup_files"].append({
                    "name": backup_file.name,
                    "size": size,
                    "size_mb": round(size / 1024 / 1024, 2),
                    "modified": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
                })
                stats["total_size"] += size
                
            stats["total_size_mb"] = round(stats["total_size"] / 1024 / 1024, 2)
            
            return stats
            
        except Exception as e:
            print(f"⚠️ [Log Rotation] 통계 조회 오류: {str(e)}")
            return {"error": str(e)}


# 전역 로그 로테이션 인스턴스
_log_rotation = None


def get_log_rotation():
    """로그 로테이션 인스턴스 반환 (싱글톤).
    
    환경 변수에서 설정을 읽어옵니다.
    """
    global _log_rotation
    if _log_rotation is None:
        # 환경 변수에서 설정 읽기
        max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        retention_days = int(os.getenv("LOG_RETENTION_DAYS", "30"))
        check_interval = int(os.getenv("LOG_CHECK_INTERVAL", "3600"))  # 1시간
        
        _log_rotation = LogRotation(
            max_bytes=max_bytes,
            backup_count=backup_count,
            retention_days=retention_days,
            check_interval=check_interval
        )
    return _log_rotation
