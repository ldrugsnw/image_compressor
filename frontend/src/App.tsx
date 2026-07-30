import { ChangeEvent, FormEvent, useEffect, useState } from "react";


const MAX_UPLOAD_SIZE_BYTES = 10_000_000;
const API_URL =
  "https://didactic-potato-7v7wxxqvgx5p347w-8000.app.github.dev/images/compress";


function formatFileSize(sizeInBytes: number) {
  if (sizeInBytes >= 1_000_000) {
    return `${(sizeInBytes / 1_000_000).toFixed(2)} MB`;
  }

  return `${(sizeInBytes / 1_000).toFixed(1)} KB`;
}


function App() {
  const [file, setFile] = useState<File | null>(null);
  const [targetSizeKb, setTargetSizeKb] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");
  const [downloadName, setDownloadName] = useState("");
  const [compressedSize, setCompressedSize] = useState<number | null>(null);

  useEffect(() => {
    return () => {
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl);
      }
    };
  }, [downloadUrl]);

  function clearDownload() {
    setDownloadUrl("");
    setDownloadName("");
    setCompressedSize(null);
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    setError("");
    clearDownload();

    if (selectedFile && selectedFile.size > MAX_UPLOAD_SIZE_BYTES) {
      setFile(null);
      setError("파일 용량은 10 MB 이하여야 합니다.");
      event.target.value = "";
      return;
    }

    if (
      selectedFile &&
      !["image/jpeg", "image/jpg"].includes(selectedFile.type)
    ) {
      setFile(null);
      setError("JPEG 파일만 선택할 수 있습니다.");
      event.target.value = "";
      return;
    }

    setFile(selectedFile);
  }

  async function readErrorMessage(response: Response): Promise<string> {
    try {
      const body = (await response.json()) as { detail?: string };
      return body.detail ?? "압축 요청에 실패했습니다.";
    } catch {
      return "압축 요청에 실패했습니다.";
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    clearDownload();

    const parsedTargetSize = Number(targetSizeKb);
    if (!file) {
      setError("JPEG 파일을 선택해 주세요.");
      return;
    }
    if (!Number.isInteger(parsedTargetSize) || parsedTargetSize <= 0) {
      setError("목표 용량은 0보다 큰 정수여야 합니다.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_size_kb", String(parsedTargetSize));

    setIsLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const compressedBlob = await response.blob();
      setDownloadUrl(URL.createObjectURL(compressedBlob));
      setDownloadName(`${file.name.replace(/\.[^.]+$/, "")}_compressed.jpg`);
      setCompressedSize(compressedBlob.size);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "압축 요청에 실패했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main>
      <h1>Image Compressor</h1>
      <p>JPEG 이미지 한 장을 원하는 최대 용량 이하로 압축합니다.</p>

      <form onSubmit={handleSubmit}>
        <label>
          JPEG 이미지
          <input
            type="file"
            accept="image/jpeg,.jpg,.jpeg"
            onChange={handleFileChange}
          />
        </label>

        {file && (
          <p className="file-info">
            {file.name} · {formatFileSize(file.size)}
          </p>
        )}

        <label>
          목표 용량 (KB)
          <input
            type="number"
            min="1"
            step="1"
            value={targetSizeKb}
            onChange={(event) => {
              setTargetSizeKb(event.target.value);
              setError("");
              clearDownload();
            }}
            placeholder="예: 500"
          />
        </label>

        <button type="submit" disabled={isLoading}>
          {isLoading ? "압축 중..." : "압축하기"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {downloadUrl && compressedSize !== null && file && (
        <>
          <p>
            압축 완료: {formatFileSize(file.size)} →{" "}
            {formatFileSize(compressedSize)}
            <br />
            {file.size === compressedSize
              ? "파일 크기가 변경되지 않았습니다."
              : `${((1 - compressedSize / file.size) * 100).toFixed(1)}% 감소`}
          </p>
          <a className="download" href={downloadUrl} download={downloadName}>
            압축된 이미지 다운로드
          </a>
        </>
      )}
    </main>
  );
}

export default App;
