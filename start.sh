# Kill anything on port 8000 and 5173 first
echo "Cleaning up ports..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
pkill -f "uvicorn backend.app.main:app" 2>/dev/null

# Start backend in background
source venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend (using node path if needed)
export PATH="/opt/homebrew/opt/node/bin:$PATH"
cd frontend
npm run dev -- --host &
FRONTEND_PID=$!

# Trap Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT

echo "==========================================="
echo "MTG Rulebook AI Web App Running"
echo "==========================================="
echo "backend: http://localhost:8000/api/docs"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both servers."

wait
