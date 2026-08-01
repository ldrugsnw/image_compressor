import {
  ChangeEvent,
  DragEvent,
  FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";


const MAX_UPLOAD_SIZE_BYTES = 10_000_000;
const API_URL = "/api/images/compress";
const SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/webp"];


type ResizeProposal = {
  message: string;
  originalWidth: number;
  originalHeight: number;
  suggestedWidth: number;
  suggestedHeight: number;
};


function formatFileSize(sizeInBytes: number) {
  if (sizeInBytes >= 1_000_000) {
    return `${(sizeInBytes / 1_000_000).toFixed(2)} MB`;
  }

  return `${(sizeInBytes / 1_000).toFixed(1)} KB`;
}

function isSupportedImageFile(file: File) {
  if (SUPPORTED_IMAGE_TYPES.includes(file.type)) {
    return true;
  }

  return file.type === "" && /\.(jpe?g|webp)$/i.test(file.name);
}

function getErrorDetail(detail: unknown): string | null {
  if (typeof detail === "string") {
    return detail;
  }

  if (
    typeof detail === "object" &&
    detail !== null &&
    "message" in detail &&
    typeof detail.message === "string"
  ) {
    return detail.message;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (
          typeof item === "object" &&
          item !== null &&
          "msg" in item &&
          typeof item.msg === "string"
        ) {
          const location =
            "loc" in item && Array.isArray(item.loc)
              ? item.loc
                  .filter((part: unknown) => part !== "body")
                  .join(".")
              : "";

          return location ? `${location}: ${item.msg}` : item.msg;
        }

        return null;
      })
      .filter((message): message is string => message !== null);

    return messages.length > 0 ? messages.join(", ") : null;
  }

  return null;
}


function getResizeProposal(detail: unknown): ResizeProposal | null {
  if (
    typeof detail !== "object" ||
    detail === null ||
    !("code" in detail) ||
    detail.code !== "resize_required" ||
    !("message" in detail) ||
    typeof detail.message !== "string" ||
    !("original_width" in detail) ||
    typeof detail.original_width !== "number" ||
    !("original_height" in detail) ||
    typeof detail.original_height !== "number" ||
    !("suggested_width" in detail) ||
    typeof detail.suggested_width !== "number" ||
    !("suggested_height" in detail) ||
    typeof detail.suggested_height !== "number"
  ) {
    return null;
  }

  return {
    message: detail.message,
    originalWidth: detail.original_width,
    originalHeight: detail.original_height,
    suggestedWidth: detail.suggested_width,
    suggestedHeight: detail.suggested_height,
  };
}


function App() {
  const [file, setFile] = useState<File | null>(null);
  const [targetSizeKb, setTargetSizeKb] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [resizeProposal, setResizeProposal] = useState<ResizeProposal | null>(
    null,
  );
  const [originalPreviewUrl, setOriginalPreviewUrl] = useState("");
  const [originalDimensions, setOriginalDimensions] = useState<{
    width: number;
    height: number;
  } | null>(null);
  const [downloadUrl, setDownloadUrl] = useState("");
  const [downloadName, setDownloadName] = useState("");
  const [compressedSize, setCompressedSize] = useState<number | null>(null);
  const [compressedDimensions, setCompressedDimensions] = useState<{
    width: number;
    height: number;
  } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragEnterCount = useRef(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) {
      setOriginalPreviewUrl("");
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    setOriginalPreviewUrl(previewUrl);

    return () => {
      URL.revokeObjectURL(previewUrl);
    };
  }, [file]);

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
    setCompressedDimensions(null);
    setResizeProposal(null);
  }

  function selectFile(selectedFile: File | null) {
    setError("");
    setOriginalDimensions(null);
    clearDownload();

    if (selectedFile && selectedFile.size > MAX_UPLOAD_SIZE_BYTES) {
      setFile(null);
      setError("파일 용량은 10 MB 이하여야 합니다.");
      return false;
    }

    if (
      selectedFile &&
      !isSupportedImageFile(selectedFile)
    ) {
      setFile(null);
      setError("JPEG 또는 WebP 파일만 선택할 수 있습니다.");
      return false;
    }

    setFile(selectedFile);
    return true;
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;

    if (!selectFile(selectedFile)) {
      event.target.value = "";
    }
  }

  async function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    dragEnterCount.current = 0;
    setIsDragging(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    const fileFromItem =
      Array.from(event.dataTransfer.items)
        .find((item) => item.kind === "file")
        ?.getAsFile() ?? null;
    const droppedFile = fileFromItem ?? event.dataTransfer.files[0] ?? null;

    if (!droppedFile) {
      setFile(null);
      setError("드롭한 파일을 읽을 수 없습니다.");
      clearDownload();
      return;
    }

    try {
      const fileType =
        droppedFile.type ||
        (/\.jpe?g$/i.test(droppedFile.name)
          ? "image/jpeg"
          : /\.webp$/i.test(droppedFile.name)
            ? "image/webp"
            : "");
      const stableFile = new File(
        [await droppedFile.arrayBuffer()],
        droppedFile.name,
        {
          type: fileType,
          lastModified: droppedFile.lastModified,
        },
      );

      selectFile(stableFile);
    } catch {
      setFile(null);
      setError("드롭한 파일을 읽을 수 없습니다.");
      clearDownload();
    }
  }

  async function readErrorResponse(response: Response): Promise<{
    message: string;
    resizeProposal: ResizeProposal | null;
  }> {
    try {
      const body = (await response.json()) as { detail?: unknown };
      return {
        message: getErrorDetail(body.detail) ?? "압축 요청에 실패했습니다.",
        resizeProposal: getResizeProposal(body.detail),
      };
    } catch {
      return {
        message: "압축 요청에 실패했습니다.",
        resizeProposal: null,
      };
    }
  }

  async function requestCompression(allowResize: boolean) {
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
    formData.append("allow_resize", String(allowResize));

    setIsLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const responseError = await readErrorResponse(response);

        if (responseError.resizeProposal) {
          setResizeProposal(responseError.resizeProposal);
          return;
        }

        throw new Error(responseError.message);
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

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void requestCompression(false);
  }

  return (
    <main>
      <h1>Image Compressor</h1>
      <p>JPEG 또는 정적 불투명 WebP 한 장을 JPEG로 압축합니다.</p>

      <form onSubmit={handleSubmit}>
        <div className="file-field">
          <label htmlFor="image-file">JPEG 또는 WebP 이미지</label>
          <div
            className={`drop-zone${isDragging ? " dragging" : ""}`}
            onDragEnter={(event) => {
              event.preventDefault();
              event.stopPropagation();
              dragEnterCount.current += 1;
              setIsDragging(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              event.stopPropagation();
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              event.stopPropagation();
              dragEnterCount.current = Math.max(0, dragEnterCount.current - 1);

              if (dragEnterCount.current === 0) {
                setIsDragging(false);
              }
            }}
            onDrop={handleDrop}
          >
            <span>JPEG 또는 WebP 이미지를 이곳에 끌어다 놓으세요.</span>
          </div>
          <div className="file-picker">
            <button
              className="file-select-button"
              type="button"
              onClick={() => fileInputRef.current?.click()}
            >
              파일 선택
            </button>
            <span className="selected-file-name">
              {file?.name ?? "선택한 파일 없음"}
            </span>
          </div>
          <input
            ref={fileInputRef}
            className="file-input"
            id="image-file"
            type="file"
            accept="image/jpeg,image/webp,.jpg,.jpeg,.webp"
            onChange={handleFileChange}
          />
        </div>

        {file && (
          <p className="file-info">
            파일 용량: {formatFileSize(file.size)}
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

      {resizeProposal && (
        <section className="resize-confirmation" aria-live="polite">
          <p>{resizeProposal.message}</p>
          <p className="resize-dimensions">
            {resizeProposal.originalWidth} × {resizeProposal.originalHeight} px
            {" → "}
            {resizeProposal.suggestedWidth} × {resizeProposal.suggestedHeight} px
          </p>
          <div className="resize-actions">
            <button
              className="resize-approve"
              type="button"
              disabled={isLoading}
              onClick={() => void requestCompression(true)}
            >
              해상도 축소 후 압축
            </button>
            <button
              className="resize-reject"
              type="button"
              disabled={isLoading}
              onClick={() => {
                setResizeProposal(null);
                setError("해상도 축소를 취소했습니다.");
              }}
            >
              거절
            </button>
          </div>
        </section>
      )}

      {file && originalPreviewUrl && (
        <div className={`previews${downloadUrl ? "" : " single"}`}>
          <figure>
            <figcaption>
              원본
              {originalDimensions &&
                ` · ${originalDimensions.width} × ${originalDimensions.height} px`}
            </figcaption>
            <img
              src={originalPreviewUrl}
              alt="압축 전 원본"
              onLoad={(event) => {
                setOriginalDimensions({
                  width: event.currentTarget.naturalWidth,
                  height: event.currentTarget.naturalHeight,
                });
              }}
            />
          </figure>
          {downloadUrl && compressedSize !== null && (
            <figure>
              <figcaption>
                압축 결과
                {compressedDimensions &&
                  ` · ${compressedDimensions.width} × ${compressedDimensions.height} px`}
              </figcaption>
              <img
                src={downloadUrl}
                alt="압축 결과"
                onLoad={(event) => {
                  setCompressedDimensions({
                    width: event.currentTarget.naturalWidth,
                    height: event.currentTarget.naturalHeight,
                  });
                }}
              />
            </figure>
          )}
        </div>
      )}

      {downloadUrl && compressedSize !== null && file && (
        <>
          <p className="compression-summary">
            압축 완료: {formatFileSize(file.size)} →{" "}
            {formatFileSize(compressedSize)}
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
