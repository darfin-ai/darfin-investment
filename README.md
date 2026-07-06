## 실행 방법

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env에 DART_API_KEY, GEMINI_API_KEY 확인/설정

uvicorn main:app --host 127.0.0.1 --port 8001
```