import { useState, useRef } from "react"

import { SlCloudUpload } from "react-icons/sl"

interface FileUploadButtonProps {
  onFilesSelected?: (files: File[]) => void
}

const FileUploadButton = ({ onFilesSelected }: FileUploadButtonProps) => {
  const [isLoading, setIsLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    setIsLoading(true)

    const files = event.target.files
    if (files && files.length > 0 && onFilesSelected) {
      // FileList를 File 배열로 변환
      const fileArray = Array.from(files)
      onFilesSelected(fileArray)
    }

    // input 초기화 (같은 파일을 다시 선택할 수 있도록)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }

    setIsLoading(false)
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  // 사이드 패널의 부모 컨테이너 너비에서 양쪽 여백(7px * 2)을 뺀 크기
  const horizontalPadding = 7.0

  return (
    <>
      {/* 숨겨진 파일 입력 */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".jpg,.jpeg,.png,.mp4,.mp3"
        onChange={handleFileSelect}
        style={{ display: "none" }}
      />

      {/* 업로드 버튼 */}
      <div
        onClick={handleButtonClick}
        style={{
          width: `calc(100% - ${horizontalPadding * 2}px)`,
          height: 190,
          margin: `0 ${horizontalPadding}px`,
          backgroundColor: "white",
          borderRadius: 15,
          border: "2px solid rgba(39, 0, 93, 1)",
          boxShadow: "0px 3px 8px rgba(0, 0, 0, 0.1)",
          cursor: "pointer",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 14
        }}>
        {/* 아이콘 또는 로딩 표시 */}
        {isLoading ? (
          <div
            style={{
              width: 40,
              height: 40,
              border: "3px solid rgba(39, 0, 93, 1)",
              borderTopColor: "transparent",
              borderRadius: "50%",
              animation: "spin 1s linear infinite"
            }}
          />
        ) : (
          <SlCloudUpload
            style={{
              fontSize: 40,
              color: "rgba(148, 0, 255, 1)"
            }}
          />
        )}

        {/* 제목 */}
        <span
          style={{
            color: "rgba(39, 0, 93, 1)",
            fontSize: 22,
            fontFamily: "'K2D', sans-serif",
            fontWeight: 500,
            lineHeight: 1,
            textAlign: "center"
          }}>
          Select File to Upload
        </span>

        {/* 설명 */}
        <span
          style={{
            color: "rgba(39, 0, 93, 0.41)",
            fontSize: 14,
            fontFamily: "'K2D', sans-serif",
            fontWeight: 500,
            lineHeight: 1.22,
            textAlign: "center"
          }}>
          지원 파일 형식: JPG, PNG, MP4, MP3
        </span>
      </div>

      {/* 로딩 애니메이션 스타일 */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </>
  )
}

export default FileUploadButton

