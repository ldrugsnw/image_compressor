# Image Compressor 작업 인수인계

마지막 업데이트: 2026-07-27

## 현재 상태

JPEG 한 장을 선택하고 목표 용량을 입력하여 FastAPI 서버에 전송한 뒤,
압축된 JPEG를 다운로드하는 MVP 코드가 구현되어 있습니다.

구현된 주요 파일:

- `backend/app/main.py`: FastAPI 엔드포인트, 입력 검증, CORS, JPEG 응답
- `backend/app/compressor.py`: JPEG 검증, EXIF 방향 보정, quality 이진 탐색
- `frontend/src/App.tsx`: 파일 선택, FormData 요청, 오류 표시, Blob 다운로드

기존 확인 결과:

- Pillow 압축 및 결과 JPEG 재열기 성공
- 실제 multipart HTTP 요청 성공
- 프론트엔드 TypeScript/Vite 빌드 성공
- 잘못된 파일과 목표 용량 오류 응답 확인

## 현재 사용자 증상

사용자가 직접 JPEG 파일을 선택해 실행했을 때 화면에 다음 메시지가 표시됩니다.

```text
Load Failed
```

아직 이 증상의 실제 원인은 진단하지 않았습니다.

## 다음 작업의 목표

기능을 추가하지 말고 `Load Failed`의 원인만 먼저 진단합니다.

가장 먼저 다음 정보를 확인합니다.

1. FastAPI와 Vite 개발 서버가 모두 실행 중인지 확인
2. 브라우저 개발자 도구의 Network 탭에서
   `POST /images/compress` 요청이 생성되는지 확인
3. 요청 URL, 상태 코드, 응답 본문 또는 CORS 메시지 확인
4. FastAPI 터미널에 해당 요청 로그가 도착하는지 확인
5. Codespaces 또는 원격 개발 환경이라면
   `frontend/src/App.tsx`의 `http://localhost:8000`이
   브라우저에서 접근 가능한 주소인지 확인

현재 프론트엔드 API 주소:

```ts
const API_URL = "http://localhost:8000/images/compress";
```

현재 백엔드 CORS 허용 주소:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Codespaces의 포트 전달 주소로 프론트엔드를 열었다면 브라우저 Origin이 위 주소와
다르기 때문에 CORS 또는 API 주소 문제가 생길 수 있습니다. 실제 Network 기록을
확인하기 전에는 원인으로 단정하거나 코드를 수정하지 않습니다.

## 실행 명령

백엔드:

```bash
cd /workspaces/image_compressor
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload
```

프론트엔드:

```bash
cd /workspaces/image_compressor
npm install --prefix frontend
npm run dev --prefix frontend
```

## 사용자에게 요청하면 유용한 정보

다음 작업 때 가능하면 아래 내용을 받습니다.

- 브라우저 주소창에 표시되는 프론트엔드 전체 주소
- 브라우저 개발자 도구 Network 탭의 실패 요청 상태
- Console 탭의 오류 문장
- 백엔드 터미널에 `POST /images/compress` 로그가 나타났는지 여부

비밀 키나 개인 이미지 자체는 공유할 필요가 없습니다.

## 작업 범위

다음 단계에서는 원인 진단과 필요한 최소 수정만 진행합니다.
로그인, 데이터베이스, 다중 이미지, PNG/WebP, 배포 자동화 등은 추가하지 않습니다.
