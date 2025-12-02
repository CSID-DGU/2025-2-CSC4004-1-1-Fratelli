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
      const fileArray = Array.from(files)
      onFilesSelected(fileArray)
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }

    setIsLoading(false)
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  const horizontalPadding = 7.0

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".jpg,.jpeg,.png,.bmp,.gif,.webp,.mp4,.mov,.mkv,.avi,.webm"
        onChange={handleFileSelect}
        style={{ display: "none" }}
      />

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

        <span
          style={{
            color: "rgba(39, 0, 93, 0.41)",
            fontSize: 12,
            fontFamily: "'K2D', sans-serif",
            fontWeight: 500,
            lineHeight: 1.22,
            textAlign: "center"
          }}>
          지원 파일 형식: JPG, JPEG, PNG, MP4, MOV 등
        </span>
      </div>

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

