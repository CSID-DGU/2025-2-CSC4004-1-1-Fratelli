import { useState, useEffect } from "react"

import FilterButton from "../../../components/file/history/filterButton"
import {
  GoImage,
  GoVideo,
  GoDownload,
  GoTrash,
  GoFileDirectory,
  GoPlay,
  GoAlert
} from "react-icons/go"
import {
  deleteFile as deleteFileApi,
  downloadFile as downloadFileApi,
  getFiles
} from "../../../services/file/file.service"
import type { FileListItem } from "../../../services/file/file.service"

type FileItem = FileListItem

interface FileHistoryPageProps {
  refreshTrigger?: number
  isLoggedIn?: boolean
  logoutVersion?: number
}

const FileHistoryPage = ({
  refreshTrigger,
  isLoggedIn = false,
  logoutVersion
}: FileHistoryPageProps) => {
  const [selectedTab, setSelectedTab] = useState(0)
  const [files, setFiles] = useState<FileItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const tabs = ["ALL", "사진", "동영상"]

  const handlePreviewError = (index: number) => {
    setFiles((prev) =>
      prev.map((file, i) =>
        i === index
          ? {
              ...file,
              previewUrl: undefined
            }
          : file
      )
    )
  }

  useEffect(() => {
    if (!isLoggedIn) {
      setFiles([])
      setIsLoading(false)
      setErrorMessage(null)
      return
    }

    loadFiles()
  }, [selectedTab, refreshTrigger, isLoggedIn])

  useEffect(() => {
    if (logoutVersion !== undefined) {
      setFiles([])
      setIsLoading(false)
      setErrorMessage(null)
    }
  }, [logoutVersion])

  const loadFiles = async () => {
    setIsLoading(true)
    setErrorMessage(null)

    try {
      const type =
        selectedTab === 1 ? "image" : selectedTab === 2 ? "video" : undefined

      const fetchedFiles = await getFiles(type)
      setFiles(fetchedFiles)
      setIsLoading(false)
    } catch (e) {
      setIsLoading(false)
      setErrorMessage(
        e instanceof Error
          ? e.message.replace("Exception: ", "")
          : "파일을 불러오는데 실패했습니다."
      )
    }
  }

  const deleteFile = async (taskId: string, index: number) => {
    try {
      await deleteFileApi(taskId)
      setFiles((prev) => prev.filter((_, i) => i !== index))
      alert("파일이 삭제되었습니다.")
    } catch (e) {
      alert(
        `파일 삭제 실패: ${
          e instanceof Error ? e.message.replace("Exception: ", "") : "알 수 없는 오류"
        }`
      )
    }
  }

  const downloadFile = async (taskId: string, fileName: string) => {
    if (!taskId) {
      alert("다운로드할 수 없는 파일입니다.")
      return
    }

    try {
      await downloadFileApi(taskId, fileName)
    } catch (e) {
      alert(
        `다운로드 실패: ${
          e instanceof Error ? e.message.replace("Exception: ", "") : "알 수 없는 오류"
        }`
      )
    }
  }

  const handleFileClick = async (file: FileItem) => {
    downloadFile(file.taskId, file.fileName)
  }

  const handleFileRightClick = (file: FileItem, index: number) => {
    const confirmDelete = confirm(
      `${file.fileName}\n\n정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`
    )

    if (confirmDelete) {
      void deleteFile(file.taskId, index)
    }
  }

  const buildPlaceholder = (fileType: "image" | "video", fileName: string, color: string) => {
    const Icon = fileType === "video" ? GoVideo : GoImage
    const displayName = fileName.length > 10 ? `${fileName.substring(0, 10)}...` : fileName

    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          backgroundColor: color,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: 8
        }}>
        <Icon
          style={{
            fontSize: 50,
            color: "rgba(128, 128, 128, 0.7)"
          }}
        />
        <div style={{ height: 8 }} />
        <span
          style={{
            fontSize: 10,
            color: "rgba(128, 128, 128, 0.6)",
            fontFamily: "'K2D', sans-serif",
            textAlign: "center",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            maxWidth: "100%"
          }}>
          {displayName}
        </span>
      </div>
    )
  }

  // 히스토리 필터 버튼과 동일한 보라색 계열로 카드 배경 통일
  const colors = ["rgba(39, 0, 93, 1)"]

  return (
    <div
      style={{
        backgroundColor: "white",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden"
      }}>
      <div
        style={{
          padding: "16px 24px 24px 24px"
        }}>
        <div
          style={{
            display: "flex",
            gap: 6,
            width: "100%"
          }}>
          {tabs.map((tab, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                minWidth: 0
              }}>
              <FilterButton
                title={tab}
                isSelected={selectedTab === i}
                onTap={() => {
                  setSelectedTab(i)
                }}
              />
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "0 24px 24px 24px"
        }}>
        {isLoading ? (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: "100%"
            }}>
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
          </div>
        ) : errorMessage ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              gap: 16
            }}>
            <GoAlert
              style={{
                fontSize: 48,
                color: "#ef5350"
              }}
            />
            <span
              style={{
                fontSize: 14,
                fontFamily: "'K2D', sans-serif",
                color: "rgba(128, 128, 128, 0.6)",
                textAlign: "center"
              }}>
              {errorMessage}
            </span>
            <button
              onClick={loadFiles}
              style={{
                padding: "8px 16px",
                backgroundColor: "rgba(39, 0, 93, 1)",
                color: "white",
                border: "none",
                borderRadius: 8,
                cursor: "pointer",
                fontFamily: "'K2D', sans-serif",
                fontSize: 14
              }}>
              다시 시도
            </button>
          </div>
        ) : files.length === 0 ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              gap: 16
            }}>
            <GoFileDirectory
              style={{
                fontSize: 64,
                color: "rgba(128, 128, 128, 0.4)"
              }}
            />
            <span
              style={{
                fontSize: 16,
                fontFamily: "'K2D', sans-serif",
                color: "rgba(128, 128, 128, 0.6)"
              }}>
              업로드한 파일이 없습니다
            </span>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
              gap: 8,
              width: "100%",
              boxSizing: "border-box"
            }}>
            {files.map((file, index) => {
              const color = colors[index % colors.length]

              return (
                <div
                  key={file.taskId}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                    width: "100%",
                    maxWidth: "100%"
                  }}>
                  <div
                    onClick={() => handleFileClick(file)}
                    onContextMenu={(e) => {
                      e.preventDefault()
                      handleFileRightClick(file, index)
                    }}
                    style={{
                      aspectRatio: "1",
                      borderRadius: 12,
                      overflow: "hidden",
                      cursor: "pointer",
                      backgroundColor: color,
                      position: "relative",
                      width: "100%",
                      maxWidth: "100%"
                    }}>
                    {file.previewUrl ? (
                      file.fileType === "video" ? (
                        <video
                          src={file.previewUrl}
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover"
                          }}
                          muted
                          playsInline
                          preload="metadata"
                          // 자동 재생 대신 첫 프레임만 썸네일처럼 표시
                          onError={() => handlePreviewError(index)}
                        />
                      ) : (
                        <img
                          src={file.previewUrl}
                          alt={file.fileName}
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover"
                          }}
                          onError={() => handlePreviewError(index)}
                        />
                      )
                    ) : (
                      buildPlaceholder(file.fileType, file.fileName, color)
                    )}
                    {file.fileType === "video" && (
                      <div
                        style={{
                          position: "absolute",
                          top: "50%",
                          left: "50%",
                          transform: "translate(-50%, -50%)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          pointerEvents: "none"
                        }}>
                        <GoPlay
                          style={{
                            fontSize: 32,
                            color: "white",
                            marginLeft: 4,
                            filter: "drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5))"
                          }}
                        />
                      </div>
                    )}
                  </div>
                  <span
                    style={{
                      fontSize: 12,
                      fontFamily: "'K2D', sans-serif",
                      color: "rgba(29, 5, 35, 1)",
                      textAlign: "center",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      width: "100%"
                    }}>
                    {file.fileName}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  )
}

export default FileHistoryPage
