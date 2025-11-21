import {
  GoImage,
  GoVideo,
  GoDownload,
  GoX,
  GoTrash
} from "react-icons/go"

export enum UploadStatus {
  uploading = "uploading",
  done = "done",
  error = "error"
}

export enum UploadType {
  image = "image",
  video = "video"
}

interface UploadProgressButtonProps {
  fileName: string
  fileSize: string
  progress: number // 0 ~ 1 (0 ~ 100%)
  status: UploadStatus
  type: UploadType
  onDownload?: () => void
  onDelete?: () => void
}

const UploadProgressButton = ({
  fileName,
  fileSize,
  progress,
  status,
  type,
  onDownload,
  onDelete
}: UploadProgressButtonProps) => {
  const horizontalPadding = 7.0

  const getLeftIcon = () => {
    switch (type) {
      case UploadType.image:
        return <GoImage style={{ fontSize: 18, color: "rgba(29, 5, 35, 1)" }} />
      case UploadType.video:
        return <GoVideo style={{ fontSize: 18, color: "rgba(29, 5, 35, 1)" }} />
      default:
        return "📄"
    }
  }

  const isUploading = status === UploadStatus.uploading
  const iconTop = isUploading ? 12 : 18
  const fileNameTop = isUploading ? 13 : 19
  const fileSizeTop = isUploading ? 15 : 21

  return (
    <div
      style={{
        width: `calc(100% - ${horizontalPadding * 2}px)`,
        height: 56,
        margin: `0 ${horizontalPadding}px 10px ${horizontalPadding}px`,
        backgroundColor: "white",
        borderRadius: 12,
        border: "0.5px solid #808080",
        boxShadow: "0px 3px 6px rgba(0, 0, 0, 0.05)",
        position: "relative"
      }}>
      <div
        style={{
          position: "absolute",
          left: 10,
          top: iconTop,
          width: 24,
          height: 24,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 18
        }}>
        {getLeftIcon()}
      </div>

      <div
        style={{
          position: "absolute",
          left: 38,
          top: fileNameTop,
          color: "rgba(29, 5, 35, 1)",
          fontSize: 13,
          fontFamily: "'K2D', sans-serif",
          fontWeight: 500,
          lineHeight: 1.69,
          maxWidth: "calc(100% - 160px)",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap"
        }}>
        {fileName}
      </div>

      <div
        style={{
          position: "absolute",
          right: 70,
          top: fileSizeTop,
          color: "rgba(162, 162, 162, 1)",
          fontSize: 10,
          fontFamily: "'K2D', sans-serif",
          fontWeight: 500,
          lineHeight: 2.2
        }}>
        {fileSize}
      </div>

      {status === UploadStatus.uploading && (
        <div
          style={{
            position: "absolute",
            right: 34,
            top: 16,
            color: "rgba(29, 5, 35, 1)",
            fontSize: 10,
            fontFamily: "'K2D', sans-serif",
            fontWeight: 500
          }}>
          {Math.round(progress * 100)}%
        </div>
      )}

      {(status === UploadStatus.done || status === UploadStatus.uploading) && (
        <div
          style={{
            position: "absolute",
            right: 10,
            top: isUploading ? 14 : 17,
            display: "flex",
            gap: 0,
            alignItems: "center",
            flexDirection: "row-reverse"
          }}>
          {onDelete && (
            <button
              onClick={onDelete}
              style={{
                width: 20,
                height: 20,
                border: "none",
                backgroundColor: "transparent",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: 0,
                margin: 0
              }}>
              <GoX
                style={{
                  fontSize: 18,
                  color: "#000000", 
                  width: 18,
                  height: 18
                }}
              />
            </button>
          )}
          {status === UploadStatus.done && onDownload && (
            <button
              onClick={onDownload}
              style={{
                width: 20,
                height: 20,
                border: "none",
                backgroundColor: "transparent",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: 0,
                margin: 0
              }}>
              <GoDownload
                style={{
                  fontSize: 18,
                  color: "rgba(29, 5, 35, 1)",
                  width: 18,
                  height: 18
                }}
              />
            </button>
          )}
        </div>
      )}

      {status === UploadStatus.error && (
        <button
          onClick={onDelete}
          style={{
            position: "absolute",
            right: 8,
            top: 12,
            width: 32,
            height: 32,
            border: "none",
            backgroundColor: "transparent",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 20,
            color: "#ef5350",
            padding: 0
          }}>
          <GoTrash style={{ fontSize: 20 }} />
        </button>
      )}

      {status === UploadStatus.uploading && (
        <div
          style={{
            position: "absolute",
            left: 14,
            right: 14,
            bottom: 8,
            height: 4,
            backgroundColor: "#ECECEC",
            borderRadius: 4,
            overflow: "hidden"
          }}>
          <div
            style={{
              width: `${progress * 100}%`,
              height: "100%",
              backgroundColor: "rgba(29, 5, 35, 1)",
              transition: "width 0.3s ease"
            }}
          />
        </div>
      )}
    </div>
  )
}

export default UploadProgressButton

