@echo off
:: 개발 모드 실행 래퍼
:: 사용법:
::   dev.bat        - 백엔드만 실행
::   dev.bat full   - 백엔드 + 프론트엔드 통합 실행

call scripts\dev.bat %*
