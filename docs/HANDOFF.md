# Image Compressor 작업 인수인계

마지막 업데이트: 2026-08-02

## 프로젝트 현재 상태

Image Compressor MVP와 정적 불투명 PNG·WebP 입력 확장 기능이 정상 동작합니다.
프론트엔드는 Render Static Site, 백엔드는 Render Web Service로 공개 배포되어
GitHub `main` 브랜치의 변경을 자동 배포합니다.

사용자는 JPEG 또는 정적 불투명 PNG·WebP 이미지 한 장을 파일 선택 또는 Drag &
Drop으로 입력하고 목표 용량(KB)을 지정할 수 있습니다. PNG는 사용자가 형식
변환을 명시적으로 승인한 경우에만 JPEG로 변환합니다. 백엔드는 입력을 RGB로
변환하고 JPEG quality 60~95 범위에서 목표 이하인 가장 높은 quality를 찾습니다.
quality 조절만으로 목표를 달성할 수 없으면
서버가 비율을 유지한 예상 축소 해상도를 제시하며, 사용자가 명시적으로 승인한
경우에만 해상도를 줄여 다시 압축합니다.

현재 구현된 기능:

- JPEG 이미지 한 장 선택
- JPEG Drag & Drop 및 iPad Files 앱 호환
- 정적이며 투명 영역이 없는 WebP 입력
- WebP 입력을 JPEG 결과로 변환
- 정적이며 투명 영역이 없는 PNG 입력
- 사용자 승인 후에만 PNG 입력을 JPEG 결과로 변환
- 파일 선택 방식과 관계없이 선택한 파일명 표시
- 최대 10MB 업로드 제한
- 파일 선택 직후 원본 이미지 미리보기
- 목표 용량(KB) 입력
- JPEG quality 60~95 이진 탐색
- 압축 전후 이미지와 가로×세로 해상도 표시
- quality만으로 목표 달성 실패 시 예상 축소 해상도 안내
- 사용자의 승인 후에만 가로세로 비율을 유지한 해상도 축소
- 압축 전후 파일 용량 표시
- 압축 결과 다운로드
- 압축 요청 중 회전 아이콘과 대기 안내 표시
- 핵심 JPEG 압축 동작 자동 테스트
- 정적 불투명·투명·애니메이션 WebP 동작 자동 테스트
- Render Static Site와 Web Service 공개 배포
- 로컬 Vite 프록시와 배포용 `VITE_API_URL` 분기
- Render 프론트엔드 출처의 FastAPI CORS 허용

현재 의도적으로 구현하지 않는 기능:

- 로그인 및 회원 관리
- 데이터베이스와 압축 이력 저장
- 사용자 이미지 클라우드 저장
- 투명 또는 애니메이션 PNG 입력
- PNG 형식으로 결과를 반환하는 압축
- 투명 또는 애니메이션 WebP 입력
- 여러 이미지 동시 처리
- AI 기능
- 배포 자동화

로그인, 데이터베이스, 클라우드 저장은 단순한 미구현 항목이 아니라 현재 제품
방향의 비목표입니다. 이 서비스는 이미지를 요청 중 메모리에서만 처리하고 바로
다운로드하는 일회성 도구입니다. 압축 이력, 여러 기기 간 공유, 팀 기능 또는
과금 요구가 실제로 생길 때만 해당 기능을 다시 검토합니다. 공개 배포 후에도
이미지는 저장하지 않고 각 요청 중 메모리에서만 처리합니다.

## 주요 실행 파일

- `frontend/src/App.tsx`
  - 파일 선택 및 Drag & Drop 처리
  - JPEG·PNG·WebP 형식과 10MB 제한 검증
  - 원본 및 압축 결과 Object URL 생명주기 관리
  - 원본 즉시 미리보기와 압축 전후 해상도 표시
  - `FormData` 생성과 압축 API 요청
  - HTTP 409 형식 변환·축소 제안 해석과 승인·거절 처리
  - 압축 요청 중 `isLoading` 상태에 따른 로딩 안내 표시
  - 압축 결과 용량 표시와 다운로드
  - `VITE_API_URL`이 있으면 배포 백엔드 주소를 사용하고, 없으면 기존
    `/api/images/compress` 사용
- `frontend/src/styles.css`
  - Drag & Drop, 미리보기 및 결과 화면 스타일
  - 축소 승인 안내와 초록색 승인·빨간색 거절 버튼
  - 압축 중 회전 아이콘 애니메이션과 안내 문구 스타일
- `frontend/vite.config.ts`
  - `/api` 요청을 `http://127.0.0.1:8000`으로 전달하는 개발 프록시
- `backend/app/main.py`
  - FastAPI 애플리케이션과 `/images/compress` 엔드포인트
  - 입력 검증, 10MB 제한, CORS와 JPEG HTTP 응답
  - PNG의 JPEG 변환 승인 여부를 나타내는 `allow_format_conversion` 처리
  - 축소 승인 여부를 나타내는 `allow_resize` 처리
  - 변환 또는 축소 승인이 필요할 때 HTTP 409 반환
  - 로컬 개발 주소와 Render Static Site 주소의 CORS 허용
- `backend/app/compressor.py`
  - 실제 JPEG·PNG·WebP 형식과 손상 이미지 확인
  - PNG·WebP 애니메이션과 투명 픽셀 검사
  - PNG의 JPEG 변환 승인 확인
  - EXIF 방향 보정과 RGB 변환
  - JPEG quality 60~95 이진 탐색
  - 비율 유지 축소안 계산과 승인 후 리사이즈
- `backend/tests/test_compressor.py`
  - 메모리에서 테스트 JPEG, PNG와 WebP 생성
  - JPEG 회귀 동작과 PNG·WebP 변환 및 거절 동작 검증

## 요청부터 응답까지의 흐름

1. 사용자가 파일 선택 또는 Drag & Drop으로 JPEG, PNG나 WebP를 입력합니다.
2. 프론트엔드는 JPEG·PNG·WebP 형식과 10MB 이하인지 확인합니다.
3. Drag & Drop 파일은 바이트를 새 `File` 객체로 복사해 안정적으로 보관합니다.
4. 원본 Object URL을 만들고 이미지와 해상도를 즉시 표시합니다.
5. 사용자가 목표 용량을 양의 정수 KB로 입력합니다.
6. 프론트엔드는 `file`, `target_size_kb`, `allow_resize=false`,
   `allow_format_conversion=false`를 `FormData`에 넣어
   압축 API를 요청하고 로딩 표시를 보여줍니다.
7. 로컬에서는 `POST /api/images/compress`를 Vite 프록시가 전달합니다. 배포
   환경에서는 빌드 시 설정한 `VITE_API_URL`을 사용해 Render Web Service의
   `POST /images/compress`로 직접 요청합니다.
8. 백엔드는 목표 KB를 1000배 하여 바이트 단위로 변환합니다.
9. `compress_to_jpeg()`은 실제 JPEG·PNG·WebP 형식을 확인하고, PNG·WebP의
   애니메이션과 투명 픽셀을 거절합니다.
10. PNG는 변환 승인 전 HTTP 409와 형식 변경 정보를 반환합니다. 사용자가
    승인하면 `allow_format_conversion=true`로 다시 요청합니다.
11. JPEG quality 60~95 범위에서 목표 이하인 가장 높은 quality를 이진
    탐색합니다. PNG·WebP 입력도 결과는 JPEG입니다.
12. 성공하면 백엔드는 `image/jpeg` 바이트를 반환합니다.
13. quality 60으로도 목표를 달성할 수 없으면 비율을 유지하며 해상도를
    90%씩 줄여 실제 JPEG 인코딩 결과가 목표 이하가 되는 크기를 찾습니다.
14. 승인 전 요청에는 HTTP 409와 원본·예상 축소 해상도를 반환합니다.
15. 프론트엔드는 예상 변경을 보여주고 승인 또는 거절 버튼을 제공합니다.
16. 사용자가 승인하면 같은 파일과 목표에 `allow_resize=true`를 넣어 다시
    요청합니다.
17. 백엔드는 제안 해상도로 이미지를 줄이고 quality 60~95를 다시 탐색합니다.
18. 프론트엔드는 결과 Blob으로 미리보기와 다운로드 URL을 만들고, 압축 전후
    용량 및 해상도를 표시한 뒤 로딩 표시를 종료합니다. 오류 또는 승인 요청을
    받은 경우에도 로딩 표시는 종료됩니다.

## API

### `POST /images/compress`

`Content-Type: multipart/form-data`

요청 필드:

- `file`: JPEG 또는 정적 불투명 PNG·WebP 한 장
- `target_size_kb`: 0보다 큰 정수
- `allow_resize`: 선택 필드, 기본값 `false`
- `allow_format_conversion`: PNG의 JPEG 변환 승인, 기본값 `false`

일반 성공 응답:

- 상태: HTTP 200
- 형식: `image/jpeg`
- 내용: 목표 용량 이하의 JPEG 바이트

PNG 형식 변환 승인 필요 응답:

```json
{
  "detail": {
    "code": "format_conversion_required",
    "message": "PNG 파일은 JPEG로 변환되며 화질이 달라질 수 있습니다.",
    "original_format": "PNG",
    "result_format": "JPEG"
  }
}
```

- 상태: HTTP 409
- `allow_format_conversion=true`인 재요청에서만 JPEG로 변환합니다.

해상도 축소 승인 필요 응답:

```json
{
  "detail": {
    "code": "resize_required",
    "message": "목표 용량을 맞추려면 이미지 해상도를 줄여야 합니다.",
    "original_width": 4000,
    "original_height": 3000,
    "suggested_width": 2916,
    "suggested_height": 2187
  }
}
```

- 상태: HTTP 409
- `allow_resize=true`인 재요청에서만 실제 해상도를 변경합니다.

그 밖의 주요 오류:

- 목표 용량이 0 이하
- 빈 파일
- 10MB 초과
- JPEG, PNG 또는 WebP가 아닌 파일
- 투명 PNG
- 애니메이션 PNG
- 투명 WebP
- 애니메이션 WebP
- 손상된 이미지
- 해상도를 줄여도 달성할 수 없을 정도로 작은 목표

## 최근 구현 내용

### Render 공개 배포

프론트엔드는 Render Static Site, 백엔드는 Render Web Service로 배포했습니다.
Vite 개발 환경에서는 기존 `/api/images/compress`와 개발 프록시를 유지하고,
배포 빌드에서는 공개 백엔드 주소를 담은 `VITE_API_URL`을 사용합니다. 환경변수가
없으면 기존 로컬 주소로 동작합니다.

배포된 서비스:

```text
프론트엔드: https://image-compressor-1-4hh2.onrender.com
백엔드: https://image-compressor-icyo.onrender.com
```

FastAPI CORS에는 실제 Render Static Site 출처를 추가했습니다. Static Site에서
`VITE_API_URL`을 처음 누락해 요청이 `/api/images/compress`로 향했으나,
환경변수를 설정하고 빌드 캐시를 지운 뒤 재배포하여 해결했습니다. 배포된
JavaScript에 백엔드 주소가 포함된 것과 CORS preflight HTTP 200 응답을
확인했습니다.

관련 커밋:

```text
6b630b0 feat: 배포 환경 API 주소 지원
64fadba chore: Render 프런트 CORS 허용
```

Render 무료 Web Service는 인바운드 요청 없이 15분이 지나면 내려가며, 다음
요청에서 다시 시작하는 데 약 1분이 걸릴 수 있습니다. Static Site는 이 cold
start 대상이 아닙니다.

### 압축 요청 로딩 표시

압축 요청이 진행되는 동안 버튼 안에 CSS 회전 아이콘과 `압축 중...` 문구를
표시하고, 버튼 아래에는 서버가 이미지를 압축 중이라는 안내를 보여줍니다.
React의 기존 `isLoading` 상태를 사용하므로 요청이 성공하거나 실패하거나 HTTP
409 승인 응답을 받으면 `finally`에서 표시가 종료됩니다. 별도 라이브러리는
추가하지 않았습니다.

현재 API는 압축이 끝난 뒤 한 번에 응답하므로 실제 진행률을 프론트엔드에
전달하지 않습니다. 따라서 정확하지 않은 퍼센트 대신 요청 진행 여부만
표시합니다.

로컬 Vite 환경에서는 사용자가 회전 애니메이션을 직접 확인했습니다. 커밋을
`main`에 푸시하고 Render에서 `Clear build cache & deploy`도 실행했지만,
2026-08-02 현재 배포된 프론트 화면에서는 로딩 표시가 보이지 않았습니다.
배포 반영 여부, 브라우저 캐시 또는 표시 시간이 너무 짧은 경우를 아직 구분하지
않았으므로 다음 작업에서 원인을 확인해야 합니다.

관련 커밋:

```text
70e01ba feat: 압축 로딩 표시 추가
```

### 압축 전후 미리보기와 해상도

원본 `File`과 압축 결과 `Blob`으로 Object URL을 만들어 두 이미지를 비교합니다.
파일을 선택하면 원본을 즉시 보여주고, 압축이 성공하면 결과 이미지를 옆에
추가합니다. 각 `<img>`의 `naturalWidth`와 `naturalHeight`로 실제 픽셀
해상도를 표시합니다. 사용이 끝난 Object URL은 해제해 메모리 누수를 막습니다.

관련 커밋:

```text
9a0c861 feat: 압축 전후 이미지 미리보기 추가
ff33b33 feat: 이미지 해상도와 압축 결과 표시 개선
```

### 이미지 선택 경험 개선

브라우저 기본 파일 input의 파일명은 Drag & Drop으로 갱신되지 않으므로 숨김
input과 React의 `file` 상태를 사용하는 파일명 표시로 교체했습니다. 이제 파일
선택과 Drag & Drop이 같은 화면 상태를 사용합니다. 파일 선택 직후 원본
미리보기 또한 표시합니다.

관련 커밋:

```text
763b10d feat: 이미지 선택 경험 개선
```

### JPEG 압축 자동 테스트

`pytest`와 Pillow로 디스크 파일 없이 메모리에서 JPEG를 만들어 다음 동작을
검증합니다.

- 이미 목표 이하이면 원본 바이트 반환
- quality 조절 후 목표 용량 이하의 유효한 JPEG 반환
- 해상도 축소가 필요하면 더 작은 크기 제안
- 사용자 승인 후 실제 리사이즈 및 목표 용량 달성

관련 커밋:

```text
ce2ca7a test: JPEG 압축 알고리즘 테스트 추가
```

### 승인 기반 해상도 축소

최소 JPEG quality를 60으로 제한하여 피부색과 색상 정보가 지나치게 손상되는
것을 막습니다. quality 60으로 목표를 달성할 수 없으면 서버가 먼저 예상 축소
해상도를 계산합니다. 사용자가 초록색 승인 버튼을 누른 경우에만 비율을 유지해
리사이즈하며, 빨간색 거절 버튼을 누르면 이미지에 아무 변경도 하지 않습니다.

관련 커밋:

```text
178ffe7 feat: 승인 기반 해상도 축소 추가
```

### 정적 불투명 WebP 입력

프론트엔드는 JPEG와 함께 WebP 파일 선택 및 Drag & Drop을 허용합니다. 백엔드는
실제 이미지 형식을 확인하고, 정적이며 투명 픽셀이 없는 WebP만 RGB로 변환한 뒤
기존 JPEG quality 탐색과 승인 기반 해상도 축소를 적용합니다. 결과 형식과
다운로드 확장자는 항상 JPEG입니다. 투명 WebP와 애니메이션 WebP는 서로 다른
오류 메시지로 거절합니다.

자동 테스트는 정적 RGB·불투명 RGBA WebP 변환, 승인 기반 해상도 축소와
투명·애니메이션 WebP 거절을 검증합니다.

관련 커밋:

```text
601cf1c docs: 프로젝트 구현 범위와 문서 우선순위 정리
30a4fed feat: 정적 불투명 WebP 입력 지원
```

### 승인 기반 정적 불투명 PNG 입력

프론트엔드는 PNG 파일 선택 및 Drag & Drop을 허용합니다. 백엔드는 실제 PNG
형식, 애니메이션과 투명 픽셀을 검사합니다. 정적 불투명 PNG라도 자동으로
변환하지 않고 먼저 HTTP 409로 PNG에서 JPEG로 형식이 바뀐다는 사실을
알립니다. 사용자가 승인한 경우에만 `allow_format_conversion=true`로 다시
요청하여 JPEG로 압축합니다.

형식 변환 승인과 해상도 축소 승인은 서로 독립적이며, 둘 다 필요한 경우 최종
요청에서 두 승인 값을 함께 전달합니다. 투명 PNG와 APNG는 거절하고 결과 형식은
항상 JPEG입니다.

## 검증 결과

백엔드:

```bash
cd /workspaces/image_compressor/backend
python -m pytest -v
```

현재 열다섯 테스트가 모두 통과합니다.

```text
15 passed
```

프론트엔드:

```bash
cd /workspaces/image_compressor/frontend
npm run build
```

TypeScript 검사와 Vite 프로덕션 빌드가 통과했습니다.

로딩 표시 검증:

```text
로컬 Vite 환경: 회전 아이콘과 압축 중 안내 표시 확인
Render 배포 환경: Clear build cache & deploy 후에도 표시되지 않아 추가 확인 필요
```

Render 배포 검증:

```text
백엔드 GET / 상태 확인 성공
Render 프론트 출처의 CORS preflight HTTP 200 확인
배포된 프론트 JavaScript의 VITE_API_URL 반영 확인
사용자의 배포 환경 압축·승인·다운로드 확인
```

사용자가 실제 JPEG로 다음 흐름을 확인했습니다.

```text
JPEG 선택 또는 Drag & Drop
→ 원본 즉시 미리보기와 파일명 표시
→ quality만으로 달성할 수 없는 목표 입력
→ 원본 및 예상 축소 해상도 안내
→ 거절 시 압축하지 않음
→ 승인 시 비율 유지 해상도 축소
→ 목표 용량 이하 결과, 미리보기 및 다운로드
```

사용자가 다운로드용 WebP 테스트 파일로 다음 동작도 직접 확인했습니다.

```text
정적 불투명 WebP → JPEG 압축 및 다운로드 성공
투명 WebP → 투명 WebP 오류
애니메이션 WebP → 애니메이션 WebP 오류
```

사용자가 PNG로 다음 동작도 직접 확인했습니다.

```text
정적 불투명 PNG 선택 및 미리보기
→ JPEG 형식 변환 승인 또는 거절
→ 승인 후 JPEG 압축 및 다운로드
→ 필요한 경우 별도의 해상도 축소 승인
→ 투명 PNG와 APNG 오류
```

## 실행 방법

백엔드:

```bash
cd /workspaces/image_compressor/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

프론트엔드:

```bash
cd /workspaces/image_compressor/frontend
npm run dev -- --host 0.0.0.0
```

확인 주소:

- FastAPI 상태 확인: `http://localhost:8000`
- FastAPI API 문서: `http://localhost:8000/docs`
- Vite 프론트엔드: `http://localhost:5173`

배포 주소:

- Render 프론트엔드: `https://image-compressor-1-4hh2.onrender.com`
- Render 백엔드 상태 확인: `https://image-compressor-icyo.onrender.com`
- Render 백엔드 API 문서: `https://image-compressor-icyo.onrender.com/docs`

## Git 상태

현재 브랜치는 `main`이며 `origin/main`과 같은 커밋을 가리킵니다.

```text
70e01ba feat: 압축 로딩 표시 추가
074ad8b docs: Render 배포 상태 기록
```

현재 커밋하지 않은 추적 변경은 이 인수인계 문서의 최신화뿐입니다. 문서 커밋 후
남는 미추적 항목은 다음과 같습니다.

```text
.playwright-mcp/
.vscode/
et GITHUB_TOKEN
frontend/public/
test-files/
```

`frontend/public/`에는 사용자가 내려받아 수동 검증한 테스트 파일과 다운로드
페이지가 있습니다. 미추적 항목은 기능 또는 문서 커밋에 포함하지 않았습니다.
다음 작업에서도 사용자의 요청 없이 수정하거나 커밋하지 않습니다.

## 다음 확장 후보

현재 합의된 추가 기능은 없습니다. 실제 사용 중 불편이 발견되면 한 번에 하나의
작은 변경만 검토합니다. 여러 이미지 처리는 현재 구현 범위에 포함하지 않습니다.

## 다음 세션 시작점

1. `git status -sb`로 브랜치와 미추적 파일을 확인합니다.
2. Render 프론트엔드와 백엔드가 정상인지 확인합니다.
3. 무료 Web Service가 잠든 뒤 첫 요청에는 cold start 지연이 있을 수 있음을
   고려합니다.
4. 로컬에서는 보이지만 Render에서는 보이지 않은 압축 로딩 표시의 배포 반영
   상태를 확인합니다.
5. 코드를 변경하면 백엔드와 프론트엔드의 Render 자동 배포 결과를 확인합니다.
6. 백엔드 테스트와 프론트엔드 빌드를 실행합니다.
7. 이후 아이폰 사진 압축 실패의 정확한 오류와 실제 파일 형식을 확인합니다.
8. 실제 불편이 발견되기 전에는 새로운 기능을 추가하지 않습니다.

다음 세션에서도 `AGENTS.md` 원칙에 따라 코드를 작성하기 전에 목표, 수정 파일,
요청부터 응답까지의 흐름과 새 개념을 먼저 설명합니다.
