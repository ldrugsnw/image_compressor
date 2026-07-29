# Image Compressor 작업 인수인계

마지막 업데이트: 2026-07-29

## 프로젝트 현재 상태

Image Compressor MVP는 정상 동작하는 상태입니다.

사용자는 JPEG 이미지 한 장과 목표 용량(KB)을 입력할 수 있습니다. 프론트엔드는
두 값을 FastAPI 서버로 전송하고, 백엔드는 JPEG quality를 조절하여 목표 용량
이하의 이미지를 반환합니다. 브라우저는 응답을 Blob으로 받아 다운로드 링크를
제공합니다.

현재 MVP 범위:

- JPEG 이미지 한 장 업로드
- 목표 용량(KB) 입력
- 원본 해상도를 유지한 JPEG quality 조절
- 압축 결과 다운로드
- 압축 전후 파일 크기와 감소율 표시

현재 구현하지 않는 기능:

- 해상도 변경
- 여러 이미지 처리
- PNG 및 WebP 지원
- 로그인 및 데이터베이스
- 클라우드 저장 및 배포 자동화

## 주요 실행 파일

- `frontend/src/App.tsx`
  - JPEG 선택 및 목표 용량 입력
  - `FormData` 생성과 압축 API 요청
  - 오류 메시지 표시
  - 응답 Blob과 Object URL을 이용한 다운로드
  - 압축 전후 파일 크기와 감소율 표시
- `frontend/src/main.tsx`
  - React 애플리케이션 시작
- `backend/app/main.py`
  - FastAPI 애플리케이션과 `/images/compress` 엔드포인트
  - 입력 검증, CORS 설정, JPEG HTTP 응답
- `backend/app/compressor.py`
  - 실제 JPEG 확인과 손상된 이미지 처리
  - EXIF 방향 보정 및 RGB 변환
  - JPEG quality 이진 탐색

## 압축 요청 흐름

1. 사용자가 `frontend/src/App.tsx`에서 JPEG를 선택합니다.
2. 사용자가 목표 용량을 양의 정수 KB로 입력합니다.
3. `handleSubmit()`이 `file`과 `target_size_kb`를 `FormData`에 넣습니다.
4. 프론트엔드가 `POST /images/compress` 요청을 보냅니다.
5. `backend/app/main.py`의 `compress_image()`가 파일과 목표 용량을 받습니다.
6. 목표 KB를 1000배 하여 바이트 단위로 바꿉니다.
7. `compress_jpeg()`이 Pillow로 실제 JPEG인지 확인합니다.
8. 원본이 이미 목표 이하이면 원본 바이트를 반환합니다.
9. 그렇지 않으면 quality 1~95 범위에서 목표 이하인 가장 높은 quality를
   이진 탐색합니다.
10. quality 1에서도 목표를 달성하지 못하면
    `TargetSizeUnreachableError`를 반환합니다.
11. 성공하면 백엔드는 `image/jpeg` 바이트 응답을 반환합니다.
12. 프론트엔드는 응답을 Blob으로 읽고 다운로드용 Object URL을 만듭니다.

## 2026-07-29에 추가한 기능

압축 성공 후 다음과 같은 결과 정보를 표시하도록
`frontend/src/App.tsx`를 수정했습니다.

```text
압축 완료: 1.84 MB → 196.0 KB
89.3% 감소
```

원본이 이미 목표 용량 이하라서 서버가 원본을 그대로 반환하면 다음 메시지를
표시합니다.

```text
파일 크기가 변경되지 않았습니다.
```

구현에 사용한 값:

- 원본 크기: `file.size`
- 압축 결과 크기: `compressedBlob.size`
- 감소율: `(1 - compressedSize / file.size) * 100`

`formatFileSize()`가 바이트를 KB 또는 MB로 변환합니다. 프론트엔드와 백엔드의
기준을 맞추기 위해 `1KB = 1000바이트`, `1MB = 1,000,000바이트`를 사용합니다.

파일이나 목표 용량을 변경하면 `clearDownload()`가 이전 다운로드 URL, 파일명,
압축 결과 크기를 함께 초기화합니다.

## Git 상태

현재 작업 브랜치:

```text
agent/show-compression-results
```

오늘 기능 커밋:

```text
1abe85c feat: 압축 전후 파일 크기와 감소율 표시
```

원격 브랜치에 푸시되어 있으며 다음 Draft PR이 열려 있습니다.

- PR #1: https://github.com/ldrugsnw/image_compressor/pull/1
- 대상 브랜치: `main`
- 상태: Draft

Draft PR은 아직 `main`에 병합되지 않았습니다. 변경 내용을 확인한 다음
`Ready for review`로 전환하고 병합할 수 있습니다.

이 `docs/HANDOFF.md` 갱신은 위 커밋을 만든 뒤 수행했으므로 아직 커밋이나
Draft PR에 포함되어 있지 않습니다.

작업 전부터 저장소 루트에 다음 미추적 파일이 존재했습니다.

```text
et GITHUB_TOKEN
```

이번 작업에서는 내용을 읽거나 수정하거나 커밋하지 않았습니다. 다음 작업에서도
정체를 확인하기 전까지 자동으로 포함하지 않습니다.

## 검증 결과

프론트엔드에서 다음 명령이 성공했습니다.

```bash
cd /workspaces/image_compressor/frontend
npm run build
```

TypeScript 검사와 Vite 프로덕션 빌드가 모두 통과했습니다.

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

현재 `frontend/src/App.tsx`의 API URL과 `backend/app/main.py`의 CORS에는 특정
GitHub Codespaces 주소가 직접 작성되어 있습니다. 새 Codespace를 사용하면 주소가
달라질 수 있으므로 연결 실패 시 두 값을 먼저 확인합니다.

## 다음 세션 시작점

1. `git status -sb`로 현재 변경 상태를 확인합니다.
2. `docs/HANDOFF.md` 변경을 기존 PR에 포함할지 결정합니다.
3. PR #1의 `Files changed`에서 압축 결과 표시 변경을 확인합니다.
4. 문제가 없으면 Draft PR을 `Ready for review`로 전환한 뒤 `main`에 병합합니다.
5. 기능을 더 추가하기 전 현재 화면을 직접 실행하여 다음 두 경우를 확인합니다.
   - 원본보다 작은 목표 용량: 전후 크기와 감소율 표시
   - 원본보다 큰 목표 용량: 크기가 변경되지 않았다는 메시지 표시

새 기능 후보를 논의했지만 아직 구현하기로 결정하지 않았습니다.

- 사용자 지정 해상도 변환
- 원본과 압축 결과 이미지 비교
- JPEG quality 슬라이더

다음 세션에서도 한 번에 하나의 작은 기능만 선택하고, 구현 전에 요청부터 응답까지
데이터 흐름을 먼저 설명합니다.
