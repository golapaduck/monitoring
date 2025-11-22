#!/bin/bash

echo "========================================"
echo "  프로세스 모니터링 시스템 시작"
echo "========================================"
echo ""

echo "[1/2] 백엔드 서버 시작 중..."
cd backend && python app.py &
BACKEND_PID=$!

sleep 2

echo "[2/2] 프론트엔드 서버 시작 중..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!
echo "종료하려면 Ctrl+C를 누르세요."

# Ctrl+C 시 모든 프로세스 종료
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

wait
