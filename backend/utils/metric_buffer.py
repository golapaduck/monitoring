"""메트릭 버퍼링 시스템 (게임 서버 환경 최적화)."""

import threading
import time
import logging
from utils.database import get_connection

logger = logging.getLogger(__name__)


class MetricBuffer:
    """메트릭을 버퍼링하여 배치로 저장 (디스크 I/O 최적화)."""
    
    def __init__(self, flush_interval=10, max_size=1000):
        """메트릭 버퍼 초기화.
        
        Args:
            flush_interval: 플러시 간격 (초)
            max_size: 최대 버퍼 크기
        """
        self.buffer = []
        self.flush_interval = flush_interval
        self.max_size = max_size
        self.last_flush = time.time()
        self.lock = threading.Lock()
        self.running = False
        self.flush_thread = None
        
        logger.info(f"✅ [Metric Buffer] 초기화 (간격: {flush_interval}초, 최대: {max_size}개)")
    
    def start(self):
        """자동 플러시 스레드 시작."""
        if self.running:
            return
        
        self.running = True
        self.flush_thread = threading.Thread(
            target=self._auto_flush_loop,
            daemon=True,
            name="MetricBufferFlusher"
        )
        self.flush_thread.start()
        logger.info("✅ [Metric Buffer] 자동 플러시 시작")
    
    def stop(self):
        """자동 플러시 스레드 중지."""
        if not self.running:
            return
        
        self.running = False
        # 남은 데이터 플러시
        self.flush()
        
        if self.flush_thread and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=2)
        
        logger.info("✅ [Metric Buffer] 자동 플러시 중지")
    
    def add(self, program_id, cpu_percent, memory_mb):
        """메트릭 추가.
        
        Args:
            program_id: 프로그램 ID
            cpu_percent: CPU 사용률
            memory_mb: 메모리 사용량 (MB)
        """
        with self.lock:
            self.buffer.append({
                'program_id': program_id,
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'timestamp': time.time()
            })
            
            # 버퍼 가득 차면 즉시 플러시
            if len(self.buffer) >= self.max_size:
                self._flush_internal()
    
    def flush(self):
        """버퍼 플러시 (외부 호출용)."""
        with self.lock:
            self._flush_internal()
    
    def _flush_internal(self):
        """버퍼 플러시 (내부용, 락 필요)."""
        if not self.buffer:
            return
        
        try:
            # 배치로 한 번에 저장
            conn = get_connection()
            cursor = conn.cursor()
            
            # executemany로 배치 삽입
            cursor.executemany(
                """
                INSERT INTO resource_usage (program_id, cpu_percent, memory_mb, timestamp)
                VALUES (?, ?, ?, datetime(?, 'unixepoch'))
                """,
                [(m['program_id'], m['cpu_percent'], m['memory_mb'], m['timestamp']) 
                 for m in self.buffer]
            )
            
            conn.commit()
            conn.close()
            
            count = len(self.buffer)
            logger.debug(f"✅ [Metric Buffer] {count}개 메트릭 저장 완료")
            
            # 버퍼 초기화
            self.buffer.clear()
            self.last_flush = time.time()
            
        except Exception as e:
            logger.error(f"❌ [Metric Buffer] 플러시 오류: {str(e)}")
    
    def _auto_flush_loop(self):
        """자동 플러시 루프."""
        while self.running:
            try:
                time.sleep(1)  # 1초마다 체크
                
                current_time = time.time()
                elapsed = current_time - self.last_flush
                
                # 플러시 간격 도달 시 플러시
                if elapsed >= self.flush_interval:
                    with self.lock:
                        if self.buffer:  # 버퍼에 데이터가 있을 때만
                            self._flush_internal()
                            
            except Exception as e:
                logger.error(f"❌ [Metric Buffer] 자동 플러시 오류: {str(e)}")
    
    def get_stats(self):
        """버퍼 통계 조회.
        
        Returns:
            dict: 버퍼 통계
        """
        with self.lock:
            return {
                "buffer_size": len(self.buffer),
                "max_size": self.max_size,
                "flush_interval": self.flush_interval,
                "last_flush": self.last_flush,
                "time_since_flush": time.time() - self.last_flush
            }


# 싱글톤 인스턴스
_metric_buffer = None


def get_metric_buffer():
    """메트릭 버퍼 싱글톤 인스턴스 반환."""
    global _metric_buffer
    if _metric_buffer is None:
        _metric_buffer = MetricBuffer(flush_interval=10, max_size=1000)
        _metric_buffer.start()
    return _metric_buffer


def stop_metric_buffer():
    """메트릭 버퍼 중지."""
    global _metric_buffer
    if _metric_buffer is not None:
        _metric_buffer.stop()
        _metric_buffer = None
