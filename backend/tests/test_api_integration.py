"""API 통합 테스트.

주요 API 엔드포인트의 기능을 테스트합니다.
"""

import pytest
import json
from pathlib import Path
import sys

# 부모 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, socketio


@pytest.fixture
def client():
    """테스트 클라이언트 생성."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers(client):
    """인증 헤더 생성 (로그인 후).
    
    기본 사용자로 로그인하여 세션 쿠키를 얻습니다.
    """
    # 로그인 시도
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    })
    
    # 세션 쿠키 반환
    return {'Cookie': response.headers.get('Set-Cookie', '')}


class TestProgramsAPI:
    """프로그램 관리 API 테스트."""
    
    def test_get_programs_list(self, client, auth_headers):
        """프로그램 목록 조회 테스트."""
        response = client.get('/api/programs', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'programs' in data
        assert isinstance(data['programs'], list)
    
    def test_get_programs_unauthorized(self, client):
        """인증 없이 프로그램 목록 조회 테스트 (실패)."""
        response = client.get('/api/programs')
        
        assert response.status_code == 401
    
    def test_get_program_detail(self, client, auth_headers):
        """프로그램 상세 조회 테스트."""
        # 먼저 프로그램 목록 조회
        list_response = client.get('/api/programs', headers=auth_headers)
        programs = json.loads(list_response.data)['programs']
        
        if programs:
            program_id = programs[0]['id']
            response = client.get(f'/api/programs/{program_id}', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'program' in data
    
    def test_get_program_not_found(self, client, auth_headers):
        """존재하지 않는 프로그램 조회 테스트 (404)."""
        response = client.get('/api/programs/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False


class TestMetricsAPI:
    """메트릭 API 테스트."""
    
    def test_get_metrics(self, client, auth_headers):
        """메트릭 조회 테스트."""
        # 먼저 프로그램 목록 조회
        list_response = client.get('/api/programs', headers=auth_headers)
        programs = json.loads(list_response.data)['programs']
        
        if programs:
            program_id = programs[0]['id']
            response = client.get(f'/api/metrics/{program_id}', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'metrics' in data
            assert isinstance(data['metrics'], list)
    
    def test_get_metrics_with_hours(self, client, auth_headers):
        """시간 범위를 지정하여 메트릭 조회 테스트."""
        list_response = client.get('/api/programs', headers=auth_headers)
        programs = json.loads(list_response.data)['programs']
        
        if programs:
            program_id = programs[0]['id']
            response = client.get(
                f'/api/metrics/{program_id}?hours=12',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'metrics' in data


class TestStatusAPI:
    """상태 API 테스트."""
    
    def test_get_programs_status(self, client, auth_headers):
        """프로그램 상태 조회 테스트."""
        response = client.get('/api/programs/status', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'programs_status' in data
        assert isinstance(data['programs_status'], list)


class TestErrorHandling:
    """에러 처리 테스트."""
    
    def test_404_not_found(self, client):
        """404 Not Found 에러 처리 테스트."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error_code' in data
    
    def test_invalid_json_request(self, client, auth_headers):
        """잘못된 JSON 요청 테스트."""
        response = client.post(
            '/api/programs',
            data='invalid json',
            headers={**auth_headers, 'Content-Type': 'application/json'}
        )
        
        # 400 또는 500 에러 예상
        assert response.status_code in [400, 500]


class TestRateLimiting:
    """Rate Limiting 테스트."""
    
    def test_rate_limit_exceeded(self, client, auth_headers):
        """Rate Limit 초과 테스트."""
        # 같은 IP에서 빠르게 여러 요청 전송
        for i in range(35):  # 30 per minute 제한 초과
            response = client.get('/api/programs', headers=auth_headers)
            
            if i >= 30:
                # 30번째 이후는 Rate Limit 에러 예상
                assert response.status_code == 429


class TestCaching:
    """캐싱 테스트."""
    
    def test_programs_list_caching(self, client, auth_headers):
        """프로그램 목록 캐싱 테스트."""
        # 첫 번째 요청
        response1 = client.get('/api/programs', headers=auth_headers)
        assert response1.status_code == 200
        
        # 두 번째 요청 (캐시에서)
        response2 = client.get('/api/programs', headers=auth_headers)
        assert response2.status_code == 200
        
        # 응답 데이터 동일 확인
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        assert data1 == data2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
