# Image Compressor 작업 인수인계

마지막 업데이트: 2026-07-30

## 프로젝트 현재 상태

Image Compressor MVP는 정상 동작합니다.

현재 사용자는 JPEG 이미지 한 장을 파일 선택 또는 Drag & Drop으로 입력하고,
목표 용량(KB)을 지정할 수 있습니다. FastAPI 백엔드는 원본 해상도를 유지하면서
JPEG quality를 조절하고, 목표 용량 이하의 JPEG를 반환합니다. 프론트엔드는
압축 전후 파일 크기와 감소율을 표시하고 다운로드 링크를 제공합니다.

현재 구현된 기능:

- JPEG 이미지 한 장 선택
- JPEG Drag & Drop 업로드
- iPad Files 앱의 Drag & Drop 지원
- 최대 10MB 업로드 제한
- 목표 용량(KB) 입력
- 원본 해상도를 유지한 JPEG quality 조절
- 압축 전후 파일 크기와 감소율 표시
- 압축 결과 다운로드

현재 구현하지 않는 기능:

- 압축 전후 이미지 미리보기
- 해상도 변경
- PNG 및 WebP 지원
- 여러 이미지 처리
- 로그인 및 데이터베이스
- 클라우드 저장 및 배포 자동화

## 주요 실행 파일

- `frontend/src/App.tsx`
  - 파일 선택 및 Drag & Drop 처리
  - JPEG 형식과 10MB 제한 검증
  - 목표 용량 입력
  - `FormData` 생성과 압축 API 요청
  - FastAPI 오류 응답 표시
  - 압축 전후 용량과 감소율 표시
  - Blob과 Object URL을 이용한 다운로드
- `frontend/src/styles.css`
  - 화면 기본 스타일
  - Drag & Drop 영역과 드래그 중 강조 스타일
- `frontend/vite.config.ts`
  - `/api` 요청을 `http://127.0.0.1:8000`으로 전달하는 개발 프록시
- `backend/app/main.py`
  - FastAPI 애플리케이션과 `/images/compress` 엔드포인트
  - 입력 검증, 10MB 제한, CORS, JPEG HTTP 응답
- `backend/app/compressor.py`
  - 실제 JPEG와 손상 이미지 확인
  - EXIF 방향 보정 및 RGB 변환
  - JPEG quality 이진 탐색

## 요청부터 응답까지의 흐름

1. 사용자가 파일 선택 또는 Drag & Drop으로 JPEG를 입력합니다.
2. 프론트엔드는 JPEG 형식과 10MB 이하인지 확인합니다.
3. Drag & Drop 파일은 브라우저가 제공한 파일 바이트를 새 `File` 객체로
   복사하여 안정적으로 보관합니다.
4. 사용자가 목표 용량을 양의 정수 KB로 입력합니다.
5. `handleSubmit()`이 `file`과 `target_size_kb`를 `FormData`에 넣습니다.
6. 브라우저가 `POST /api/images/compress` 요청을 Vite에 보냅니다.
7. Vite 프록시가 `/api`를 제거하고 요청을 FastAPI의
   `POST /images/compress`로 전달합니다.
8. 백엔드는 목표 KB를 1000배 하여 바이트 단위로 변환합니다.
9. `compress_jpeg()`이 JPEG를 확인하고 quality 1~95 범위에서 목표 이하인
   가장 높은 quality를 이진 탐색합니다.
10. 성공하면 백엔드는 `image/jpeg` 바이트를 반환합니다.
11. 프론트엔드는 응답을 Blob으로 읽어 결과 용량과 감소율을 표시합니다.
12. Object URL을 사용한 다운로드 링크를 제공합니다.

## 2026-07-30에 추가한 기능

### 최대 업로드 용량 제한

프론트엔드와 백엔드 모두 원본 JPEG를 최대 10MB로 제한합니다. 프론트엔드는
요청 전에 검사하고, 백엔드는 클라이언트 검사를 신뢰하지 않고 다시 검사합니다.

관련 커밋:

```text
e2cab46 feat: 원본 이미지 업로드 용량을 10MB로 제한
```

### Drag & Drop 업로드

파일 선택 입력과 별도로 점선 Drag & Drop 영역을 추가했습니다. 드래그가 영역
내부에 머무는 동안 초록색으로 강조되고, 드롭하거나 영역 밖으로 나가면 강조가
해제됩니다.

파일 선택과 Drag & Drop은 모두 `selectFile()`을 사용하므로 JPEG 형식 검사,
10MB 제한, 이전 압축 결과 초기화가 동일하게 동작합니다.

### iPad Files 앱 호환

데스크톱 Chromium에서는 정상 동작했지만, iPad Files 앱에서 드롭한 파일을
그대로 상태에 저장하면 multipart 요청에 파일 값이 누락되는 문제가 있었습니다.

이를 해결하기 위해 다음과 같이 처리합니다.

- `DataTransfer.items`에서 파일 탐색
- 값이 없으면 `DataTransfer.files[0]` 사용
- 드롭 직후 `arrayBuffer()`로 파일 바이트 읽기
- 읽은 바이트로 새로운 `File` 객체 생성
- MIME 타입이 비어 있고 이름이 `.jpg` 또는 `.jpeg`이면 `image/jpeg` 사용

이 과정을 거친 뒤 iPad Files 앱에서 Drag & Drop 압축이 정상 동작하는 것을
확인했습니다.

### API 연결 개선

프론트엔드에 특정 Codespace의 8000번 포트 주소를 직접 작성하는 대신
`/api/images/compress`를 호출하도록 변경했습니다. Vite가 이 요청을 로컬
FastAPI 서버로 전달하므로 Codespace 이름이 바뀌어도 프론트엔드 API 주소를
수정할 필요가 없습니다.

FastAPI 검증 오류의 `detail`이 객체 배열일 때 `[object Object]`로 표시되던
문제도 수정했습니다. 이제 누락된 필드 이름과 실제 오류 문장이 표시됩니다.

관련 커밋:

```text
2bf2b31 feat: Drag & Drop 이미지 업로드 추가
```

## 검증 결과

프론트엔드에서 다음 명령이 성공했습니다.

```bash
cd /workspaces/image_compressor/frontend
npm run build
```

TypeScript 검사와 Vite 프로덕션 빌드가 모두 통과했습니다.

Playwright 브라우저 테스트에서는 다음 흐름을 확인했습니다.

```text
JPEG Drag & Drop
→ 목표 용량 입력
→ POST /api/images/compress
→ 200 OK
→ image/jpeg 응답
```

사용자 iPad의 Files 앱에서도 실제 JPEG Drag & Drop과 압축 성공을 확인했습니다.

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

Vite 프록시 설정은 개발 서버를 시작할 때 읽습니다. `vite.config.ts`를 변경한
경우 프론트엔드 개발 서버를 다시 시작해야 합니다.

## Git 상태

현재 브랜치는 `main`이며 GitHub의 `origin/main`과 같은 커밋을 가리킵니다.

```text
cd34600 Merge branch 'agent/limit-upload-size'
```

기존 작업 브랜치 두 개는 `main` 병합을 확인한 뒤 로컬과 원격에서 삭제했습니다.
현재 원격에는 `main` 브랜치만 남아 있습니다.

현재 커밋하지 않은 항목:

```text
.playwright-mcp/
et GITHUB_TOKEN
test-files/
```

이 항목들은 기능 커밋에 포함하지 않았습니다. 다음 작업에서도 용도를 확인하지
않고 자동으로 커밋하지 않습니다.

## 앞으로 개발할 기능

MVP 이후 논의한 확장 기능은 다음 세 가지입니다.

1. 압축 전후 이미지 미리보기
2. 목표 용량 달성을 위한 비율 유지 해상도 축소
3. JPEG 외 이미지 형식 지원

한 번에 하나의 작은 기능만 구현한다는 프로젝트 원칙에 따라 다음 순서를
권장합니다.

### 다음 기능: 압축 전후 이미지 미리보기

가장 먼저 원본 이미지와 압축 결과 이미지를 화면에 나란히 표시합니다. 사용자는
다운로드 전에 실제 화질 저하를 눈으로 비교할 수 있어야 합니다.

예상 데이터 흐름:

1. 선택한 원본 `File`로 Object URL 생성
2. 압축 응답 `Blob`으로 결과 Object URL 생성
3. 두 URL을 각각 `<img>`에 표시
4. 파일 변경 또는 컴포넌트 종료 시 URL 해제

이 기능은 백엔드를 변경하지 않고 프론트엔드의 Object URL 생명주기를 학습할 수
있어 다음 단계로 적합합니다.

### 그다음 기능: 승인 후 해상도 축소

JPEG quality를 최저로 낮춰도 목표 용량을 달성할 수 없을 때만 고려합니다.
가로세로 비율은 반드시 유지합니다. 서버가 임의로 해상도를 낮추면 안 되며,
예상 변경 내용을 사용자에게 알리고 승인을 받은 뒤 진행해야 합니다.

예상 흐름:

```text
quality 조절만으로 목표 달성 실패
→ 변경 전후 예상 해상도 안내
→ 사용자 승인
→ 비율을 유지해 해상도 축소
→ quality를 다시 조절
→ 압축 결과 반환
```

이 기능은 승인 전 요청과 승인 후 요청을 어떻게 나눌지 먼저 설계한 뒤
구현해야 합니다.

### 이후 기능: JPEG 외 형식 지원

PNG와 WebP 입력 지원을 검토합니다. 첫 단계에서는 PNG/WebP를 입력받고 최종
결과를 JPEG로 통일하는 방식과, 원본 형식을 유지하여 압축하는 방식 중 하나를
먼저 선택해야 합니다.

특히 투명 PNG를 JPEG로 변환하면 투명 배경이 사라지므로 배경색 처리 정책을
사용자와 먼저 결정해야 합니다. 여러 형식을 한 번에 추가하지 말고 PNG 또는
WebP 중 하나만 선택해 작은 단계로 진행하는 것이 좋습니다.

## 다음 세션 시작점

1. `git status -sb`로 미추적 파일과 현재 브랜치를 확인합니다.
2. 백엔드와 프론트엔드를 실행합니다.
3. 파일 선택과 iPad Drag & Drop 압축이 모두 정상인지 간단히 확인합니다.
4. 다음 기능으로 압축 전후 이미지 미리보기의 UI와 Object URL 흐름을 설명합니다.
5. 사용자가 흐름을 이해한 뒤 최소한의 프론트엔드 파일만 수정합니다.

다음 세션에서도 AGENTS.md의 원칙에 따라 한 번에 하나의 작은 기능만 구현하고,
코드를 작성하기 전에 목표, 수정 파일, 요청부터 응답까지의 흐름, 새 개념을 먼저
설명합니다.
