import { useEffect, useState } from "react"

import FileUploadButton from "../../../components/file/upload/fileUploadButton"
import UploadProgressButton, {
  UploadStatus,
  UploadType
} from "../../../components/file/upload/uploadPregressButton"
import {
  cancelUpload as cancelUploadApi,
  downloadFile as downloadFileApi,
  getUploadingFiles,
  uploadFile as uploadFileApi
} from "../../../services/file/file.service"

interface FileItem {
  id: string
  name: string
  size: string
  progress: number
  status: UploadStatus
  fileType: UploadType
  file?: File
  taskId?: string | null
  error?: string
}

interface FileUploadPageProps {
  onUploadSuccess?: () => void
  logoutVersion?: number
}

const FileUploadPage = ({ onUploadSuccess, logoutVersion }: FileUploadPageProps) => {
  const [files, setFiles] = useState<FileItem[]>([])

  const determineFileType = (fileName: string): UploadType => {
    const extension = fileName.toLowerCase().split(".").pop() || ""
    if (extension === "mp4" || extension === "mp3") {
      return UploadType.video
    }
    return UploadType.image
  }

  const formatFileSize = (bytes: number): string => {
    return `${(bytes / 1024).toFixed(2)} KB`
  }

  const loadUploadingFiles = async () => {
    try {
      const uploads = await getUploadingFiles()

      const serverFiles: FileItem[] = uploads.map((u) => ({
        id: u.taskId,
        name: u.fileName,
        size: formatFileSize(u.size), 
        progress:
          typeof u.progress === "number" ? u.progress / 100 : u.status === "success" ? 1 : 0,
        status:
          u.status === "success"
            ? UploadStatus.done
            : u.status === "failed"
            ? UploadStatus.error
            : UploadStatus.uploading,
        fileType: u.fileType === UploadType.video ? UploadType.video : UploadType.image,
        taskId: u.taskId
      }))

      setFiles((prev) => {
        const byTaskId = new Map(serverFiles.map((f) => [f.taskId, f]))

        const updated: FileItem[] = prev.map((f) => {
          if (!f.taskId) {
            return f
          }
          const serverFile = byTaskId.get(f.taskId)

          if (!serverFile && f.status === UploadStatus.uploading) {
            return {
              ...f,
              status: UploadStatus.done,
              progress: 1.0
            }
          }

          if (!serverFile) {
            return f
          }

          return {
            ...f,
            status: serverFile.status,
            progress: serverFile.progress
          }
        })

        const prevTaskIds = new Set(
          prev.map((f) => f.taskId).filter((id): id is string => !!id)
        )
        const additional = serverFiles.filter((f) => !prevTaskIds.has(f.taskId))

        const merged = [...updated, ...additional]

        const unique = new Map<string, FileItem>()
        for (const item of merged) {
          const key = item.taskId ?? item.id
          unique.set(key, item)
        }

        return Array.from(unique.values())
      })
    } catch (e) {
      console.error("업로드 중인 파일 목록 불러오기 실패:", e)
    }
  }

  useEffect(() => {
    void loadUploadingFiles()
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      void loadUploadingFiles()
    }, 3000) // 3초마다 갱신

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (logoutVersion !== undefined) {
      setFiles([])
    }
  }, [logoutVersion])

  const handleFilesSelected = async (selectedFiles: File[]) => {
    for (const file of selectedFiles) {
      const fileName = file.name
      const fileSize = formatFileSize(file.size)
      const fileType = determineFileType(fileName)
      const localId = `file_${Date.now()}_${Math.random()}`

      const newFile: FileItem = {
        id: localId,
        name: fileName,
        size: fileSize,
        progress: 0.0,
        status: UploadStatus.uploading,
        fileType: fileType,
        file: file,
        taskId: null
      }

      setFiles((prev) => [...prev, newFile])

      uploadFile(localId, file, fileType)
    }
  }

  const uploadFile = async (localId: string, file: File, type: UploadType) => {
    try {
      const response = await uploadFileApi(
        file,
        type === UploadType.video ? "video" : "image"
      )

      setFiles((prev) =>
        prev.map((f) =>
          f.id === localId
            ? {
                ...f,
                status: UploadStatus.done,
                progress: 1.0,
                taskId: response.taskId
              }
            : f
        )
      )

      onUploadSuccess?.()
    } catch (e) {
      setFiles((prev) => {
        return prev.map((f) => {
          if (f.id === localId) {
            return {
              ...f,
              status: UploadStatus.error,
              error: e instanceof Error ? e.message : "업로드 실패"
            }
          }
          return f
        })
      })
    }
  }

  const handleCancelUpload = async (localId: string) => {
    const file = files.find((f) => f.id === localId)
    if (!file) return

    if (!file.taskId) {
      setFiles((prev) => prev.filter((f) => f.id !== localId))
      return
    }

    try {
      await cancelUploadApi(file.taskId)
      setFiles((prev) => prev.filter((f) => f.id !== localId))
    } catch (e) {
      console.error("업로드 취소 실패:", e)
      alert(
        `업로드 취소 실패: ${
          e instanceof Error ? e.message : "알 수 없는 오류"
        }`
      )
    }
  }

  const handleDownload = async (file: FileItem) => {
    if (!file.taskId) {
      alert("다운로드할 수 없는 파일입니다.")
      return
    }

    try {
      await downloadFileApi(file.taskId, file.name)
    } catch (e) {
      alert(
        `다운로드 실패: ${
          e instanceof Error ? e.message : "알 수 없는 오류"
        }`
      )
    }
  }

  return (
    <div
      style={{
        backgroundColor: "white",
        padding: "16px 0",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden"
      }}>
      <div
        style={{
          padding: "0 24px",
          flexShrink: 0
        }}>
        <div
          style={{
            marginBottom: 4
          }}>
          <h2
            style={{
              fontSize: 22,
              fontFamily: "'K2D', sans-serif",
              color: "rgba(29, 5, 35, 1)",
              margin: 0,
              fontWeight: 600
            }}>
            Deepflect
          </h2>
        </div>

        <p
          style={{
            fontSize: 12,
            fontFamily: "'K2D', sans-serif",
            color: "rgba(179, 164, 204, 1)",
            margin: "0 0 24px 0"
          }}>
          딥페이크 생성 방지 처리를 할 파일을 업로드 해주세요
        </p>

        <FileUploadButton onFilesSelected={handleFilesSelected} />

        <div style={{ height: 24 }} />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: 12
          }}>
          <div
            style={{
              flex: 1,
              height: 1,
              backgroundColor: "rgba(162, 162, 162, 1)"
            }}
          />
          <span
            style={{
              padding: "0 12px",
              color: "rgba(162, 162, 162, 1)",
              fontSize: 14,
              fontFamily: "'K2D', sans-serif",
              fontWeight: 500
            }}>
            작업 목록
          </span>
          <div
            style={{
              flex: 1,
              height: 1,
              backgroundColor: "rgba(162, 162, 162, 1)"
            }}
          />
        </div>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "0 24px 24px 24px"
        }}>
        {files.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "40px 0",
              color: "rgba(162, 162, 162, 1)",
              fontSize: 14,
              fontFamily: "'K2D', sans-serif"
            }}>
            업로드된 파일이 없습니다.
          </div>
        ) : (
          files.map((file) => (
            <UploadProgressButton
              key={file.id}
              fileName={file.name}
              fileSize={file.size}
              progress={file.progress}
              status={file.status}
              type={file.fileType}
              onDownload={
                file.status === UploadStatus.done
                  ? () => handleDownload(file)
                  : undefined
              }
              onDelete={() => handleCancelUpload(file.id)}
            />
          ))
        )}
      </div>
    </div>
  )
}

export default FileUploadPage
