## 실행 방법

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env에 GEMINI_API_KEY 확인/설정

uvicorn main:app --host 127.0.0.1 --port 8001
```

## Render 배포

이 저장소는 Render Blueprint(`render.yaml`)로 배포할 수 있습니다.

1. GitHub/GitLab에 이 저장소를 push합니다.
2. Render Dashboard에서 `New` -> `Blueprint`를 선택하고 저장소를 연결합니다.
3. 생성 화면에서 환경변수를 입력합니다.
   - `GEMINI_API_KEY`: Gemini API 키
   - `CORS_ORIGINS`: 프론트엔드 주소. 여러 개면 쉼표로 구분합니다. 예: `https://your-frontend.onrender.com,http://localhost:5173`
4. 배포가 끝나면 Render URL의 `/`에서 상태 확인, `/docs`에서 API 문서를 확인합니다.

수동 Web Service로 만들 경우 설정값은 다음과 같습니다.

- Language: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/`
