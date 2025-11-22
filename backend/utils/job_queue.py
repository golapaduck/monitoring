"""잡/메세지 큐 시스템."""

import logging
from typing import Callable, Any, Optional, Dict
from datetime import datetime
from enum import Enum
import threading
import queue
import uuid

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """잡 상태."""
    PENDING = "pending"      # 대기 중
    RUNNING = "running"      # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"        # 실패


class Job:
    """작업 객체."""
    
    def __init__(self, func: Callable, *args, **kwargs):
        """작업 초기화.
        
        Args:
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자
        """
        self.id = str(uuid.uuid4())
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = JobStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def execute(self) -> None:
        """작업 실행."""
        try:
            self.status = JobStatus.RUNNING
            self.started_at = datetime.now()
            
            self.result = self.func(*self.args, **self.kwargs)
            self.status = JobStatus.COMPLETED
            
            logger.info(f"작업 완료: {self.id}")
        except Exception as e:
            self.status = JobStatus.FAILED
            self.error = str(e)
            logger.error(f"작업 실패 ({self.id}): {str(e)}")
        finally:
            self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "id": self.id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": (self.completed_at - self.started_at).total_seconds() 
                       if self.started_at and self.completed_at else None
        }


class JobQueue:
    """작업 큐."""
    
    def __init__(self, max_workers: int = 3):
        """작업 큐 초기화.
        
        Args:
            max_workers: 최대 워커 수
        """
        self.max_workers = max_workers
        self.queue: queue.Queue = queue.Queue()
        self.jobs: Dict[str, Job] = {}
        self.workers = []
        self.running = False
        self.lock = threading.Lock()
    
    def start(self) -> None:
        """작업 큐 시작."""
        if self.running:
            logger.warning("작업 큐가 이미 실행 중입니다")
            return
        
        self.running = True
        
        # 워커 스레드 생성
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"JobWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"작업 큐 시작: {self.max_workers}개 워커")
    
    def stop(self) -> None:
        """작업 큐 중지."""
        if not self.running:
            return
        
        self.running = False
        
        # 모든 워커 종료 대기
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        logger.info("작업 큐 중지")
    
    def submit(self, func: Callable, *args, **kwargs) -> str:
        """작업 제출.
        
        Args:
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자
            
        Returns:
            작업 ID
        """
        job = Job(func, *args, **kwargs)
        
        with self.lock:
            self.jobs[job.id] = job
        
        self.queue.put(job)
        logger.debug(f"작업 제출: {job.id}")
        
        return job.id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """작업 조회.
        
        Args:
            job_id: 작업 ID
            
        Returns:
            작업 객체 또는 None
        """
        with self.lock:
            return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """모든 작업 조회.
        
        Returns:
            작업 딕셔너리
        """
        with self.lock:
            return {
                job_id: job.to_dict()
                for job_id, job in self.jobs.items()
            }
    
    def _worker_loop(self) -> None:
        """워커 루프."""
        while self.running:
            try:
                # 타임아웃으로 주기적으로 running 체크
                job = self.queue.get(timeout=1)
                if job is None:  # 종료 신호
                    break
                
                job.execute()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"워커 오류: {str(e)}")


# 글로벌 작업 큐 인스턴스
_global_queue: Optional[JobQueue] = None


def init_job_queue(max_workers: int = 3) -> JobQueue:
    """글로벌 작업 큐 초기화.
    
    Args:
        max_workers: 최대 워커 수
        
    Returns:
        JobQueue 인스턴스
    """
    global _global_queue
    if _global_queue is None:
        _global_queue = JobQueue(max_workers)
        _global_queue.start()
    return _global_queue


def get_job_queue() -> JobQueue:
    """글로벌 작업 큐 반환.
    
    Returns:
        JobQueue 인스턴스
    """
    global _global_queue
    if _global_queue is None:
        raise RuntimeError("작업 큐가 초기화되지 않았습니다. init_job_queue()을 먼저 호출하세요.")
    return _global_queue


def submit_job(func: Callable, *args, **kwargs) -> str:
    """작업 제출.
    
    Args:
        func: 실행할 함수
        *args: 함수 인자
        **kwargs: 함수 키워드 인자
        
    Returns:
        작업 ID
    """
    queue = get_job_queue()
    return queue.submit(func, *args, **kwargs)


def close_job_queue() -> None:
    """글로벌 작업 큐 종료."""
    global _global_queue
    if _global_queue is not None:
        _global_queue.stop()
        _global_queue = None
