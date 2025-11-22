"""데이터베이스 및 설정 파일 백업 시스템."""

import os
import shutil
import gzip
import logging
from pathlib import Path
from datetime import datetime, timedelta
from utils.database import get_connection

# 로거 설정
logger = logging.getLogger(__name__)

# 백업 디렉토리
BACKUP_DIR = Path(__file__).parent.parent.parent / "data" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# 백업 보관 기간 (일)
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))


def backup_database():
    """SQLite 데이터베이스 백업.
    
    Returns:
        bool: 백업 성공 여부
    """
    try:
        from config import Config
        from utils.database import DB_PATH
        
        if not DB_PATH.exists():
            logger.warning("데이터베이스 파일이 없습니다")
            return False
        
        # 백업 파일명: monitoring_2025-11-22_14-30-45.db.gz
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = BACKUP_DIR / f"monitoring_{timestamp}.db.gz"
        
        # 데이터베이스 백업 (gzip 압축)
        with open(DB_PATH, 'rb') as f_in:
            with gzip.open(backup_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"✅ 데이터베이스 백업 완료: {backup_file.name} ({file_size:.2f}MB)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 백업 실패: {str(e)}")
        return False


def backup_config():
    """설정 파일 백업.
    
    Returns:
        bool: 백업 성공 여부
    """
    try:
        from config import USERS_JSON
        
        if not USERS_JSON.exists():
            logger.warning("설정 파일이 없습니다")
            return False
        
        # 백업 파일명: users_2025-11-22_14-30-45.json.gz
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = BACKUP_DIR / f"users_{timestamp}.json.gz"
        
        # 설정 파일 백업 (gzip 압축)
        with open(USERS_JSON, 'rb') as f_in:
            with gzip.open(backup_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        file_size = backup_file.stat().st_size / 1024  # KB
        logger.info(f"✅ 설정 파일 백업 완료: {backup_file.name} ({file_size:.2f}KB)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 설정 파일 백업 실패: {str(e)}")
        return False


def cleanup_old_backups():
    """오래된 백업 파일 삭제.
    
    Returns:
        int: 삭제된 파일 수
    """
    try:
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
        
        for backup_file in BACKUP_DIR.glob("*.gz"):
            # 파일 수정 시간 확인
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
                logger.info(f"🗑️ 오래된 백업 삭제: {backup_file.name}")
        
        if deleted_count > 0:
            logger.info(f"✅ {deleted_count}개의 오래된 백업 삭제 완료")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ 백업 정리 실패: {str(e)}")
        return 0


def restore_database(backup_file_path):
    """데이터베이스 복구.
    
    Args:
        backup_file_path: 백업 파일 경로 (str 또는 Path)
        
    Returns:
        bool: 복구 성공 여부
    """
    try:
        from utils.database import DB_PATH
        
        backup_file = Path(backup_file_path)
        
        if not backup_file.exists():
            logger.error(f"백업 파일을 찾을 수 없습니다: {backup_file}")
            return False
        
        # 현재 데이터베이스 백업 (복구 실패 시 복원용)
        if DB_PATH.exists():
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            current_backup = BACKUP_DIR / f"monitoring_current_{timestamp}.db.gz"
            with open(DB_PATH, 'rb') as f_in:
                with gzip.open(current_backup, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        # 백업 파일 복구
        with gzip.open(backup_file, 'rb') as f_in:
            with open(DB_PATH, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info(f"✅ 데이터베이스 복구 완료: {backup_file.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 복구 실패: {str(e)}")
        return False


def get_backup_list():
    """백업 파일 목록 조회.
    
    Returns:
        list: 백업 파일 정보 리스트
    """
    try:
        backups = []
        
        for backup_file in sorted(BACKUP_DIR.glob("*.gz"), reverse=True):
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size_mb": round(file_size, 2),
                "created": file_mtime.isoformat(),
                "type": "database" if "monitoring" in backup_file.name else "config"
            })
        
        return backups
        
    except Exception as e:
        logger.error(f"❌ 백업 목록 조회 실패: {str(e)}")
        return []


def perform_full_backup():
    """전체 백업 수행.
    
    Returns:
        dict: 백업 결과
    """
    logger.info("=" * 70)
    logger.info("🔄 전체 백업 시작")
    logger.info("=" * 70)
    
    result = {
        "database": backup_database(),
        "config": backup_config(),
        "cleanup": cleanup_old_backups() >= 0
    }
    
    logger.info("=" * 70)
    if all(result.values()):
        logger.info("✅ 전체 백업 완료")
    else:
        logger.warning("⚠️ 일부 백업 실패")
    logger.info("=" * 70)
    
    return result


if __name__ == "__main__":
    # 테스트용
    perform_full_backup()
