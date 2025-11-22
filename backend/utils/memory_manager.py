"""메모리 압박 감지 및 자동 정리 시스템 (게임 서버 환경)."""

import psutil
import logging
from utils.cache import get_cache

logger = logging.getLogger(__name__)


class MemoryManager:
    """메모리 압박을 감지하고 자동으로 캐시를 정리하는 관리자."""
    
    def __init__(self):
        """메모리 관리자 초기화."""
        self.critical_threshold = 90  # 90% 이상: 위험
        self.warning_threshold = 80   # 80% 이상: 경고
        self.last_cleanup = 0
        self.cleanup_cooldown = 60  # 60초마다 한 번만 정리
    
    def check_memory_pressure(self):
        """메모리 압박 감지 및 자동 정리.
        
        Returns:
            tuple: (압박 수준, 메시지)
                - "critical": 심각한 압박 (90% 이상)
                - "warning": 경고 (80-90%)
                - "normal": 정상 (80% 미만)
        """
        try:
            memory = psutil.virtual_memory()
            percent = memory.percent
            
            import time
            current_time = time.time()
            
            # Critical: 90% 이상
            if percent >= self.critical_threshold:
                # 쿨다운 체크
                if current_time - self.last_cleanup >= self.cleanup_cooldown:
                    self._cleanup_all_cache()
                    self.last_cleanup = current_time
                    logger.warning(f"⚠️ [Memory] 메모리 압박 심각 ({percent:.1f}%), 전체 캐시 정리")
                    return "critical", f"메모리 사용률 {percent:.1f}% (전체 캐시 정리됨)"
                else:
                    return "critical", f"메모리 사용률 {percent:.1f}% (정리 대기 중)"
            
            # Warning: 80-90%
            elif percent >= self.warning_threshold:
                # 쿨다운 체크
                if current_time - self.last_cleanup >= self.cleanup_cooldown:
                    self._cleanup_old_cache()
                    self.last_cleanup = current_time
                    logger.info(f"ℹ️ [Memory] 메모리 사용률 높음 ({percent:.1f}%), 오래된 캐시 정리")
                    return "warning", f"메모리 사용률 {percent:.1f}% (오래된 캐시 정리됨)"
                else:
                    return "warning", f"메모리 사용률 {percent:.1f}%"
            
            # Normal: 80% 미만
            else:
                return "normal", f"메모리 사용률 {percent:.1f}%"
                
        except Exception as e:
            logger.error(f"❌ [Memory] 메모리 압박 감지 오류: {str(e)}")
            return "error", str(e)
    
    def _cleanup_all_cache(self):
        """전체 캐시 정리 (메모리 압박 심각)."""
        try:
            cache = get_cache()
            cache.clear()
            logger.info("✅ [Memory] 전체 캐시 정리 완료")
        except Exception as e:
            logger.error(f"❌ [Memory] 캐시 정리 오류: {str(e)}")
    
    def _cleanup_old_cache(self):
        """오래된 캐시만 정리 (메모리 사용률 높음)."""
        try:
            cache = get_cache()
            # 60초 이상 된 캐시만 정리
            removed_count = 0
            import time
            current_time = time.time()
            
            # 캐시 항목 순회하며 오래된 것만 삭제
            for key in list(cache.cache.keys()):
                entry = cache.cache.get(key)
                if entry and (current_time - entry.get('timestamp', 0)) > 60:
                    cache.delete(key)
                    removed_count += 1
            
            logger.info(f"✅ [Memory] 오래된 캐시 {removed_count}개 정리 완료")
        except Exception as e:
            logger.error(f"❌ [Memory] 오래된 캐시 정리 오류: {str(e)}")
    
    def get_memory_info(self):
        """현재 메모리 정보 조회.
        
        Returns:
            dict: 메모리 정보
        """
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent": round(memory.percent, 1),
                "status": self._get_status(memory.percent)
            }
        except Exception as e:
            logger.error(f"❌ [Memory] 메모리 정보 조회 오류: {str(e)}")
            return None
    
    def _get_status(self, percent):
        """메모리 사용률에 따른 상태 반환."""
        if percent >= 90:
            return "critical"
        elif percent >= 80:
            return "warning"
        elif percent >= 70:
            return "caution"
        else:
            return "normal"


# 싱글톤 인스턴스
_memory_manager = None


def get_memory_manager():
    """메모리 관리자 싱글톤 인스턴스 반환."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
