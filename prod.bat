@echo off
:: 프로덕션 모드 실행 래퍼
:: 사용법:
::   prod.bat         - 빌드 + 배포 (기본)
::   prod.bat build   - 빌드만
::   prod.bat run     - 실행만

call scripts\prod.bat %*
