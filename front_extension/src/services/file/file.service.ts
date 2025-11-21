import { getToken } from "../../utils/storage"
import { ensureFreshAccessToken, refreshToken } from "../auth/auth.services"

const API_BASE_URL =
  process.env.PLASMO_PUBLIC_API_BASE_URL || "https://your-api.example.com"

export type FileType = "image" | "video"

export interface UploadFileResponse {
  taskId: string
  fileName: string
  fileType: FileType
  status: string
  progress?: number
  message?: string
  timestamp?: string
}

export interface FileListItem {
  taskId: string
  fileName: string
  fileType: FileType
  size: number
  url: string
  message?: string
  timestamp: string
  previewUrl?: string
}

interface RawFileListItem {
  taskId: string
  fileName: string
  fileType: string
  size: number
  url: string
  message?: string
  timestamp: string
}

interface FileListResponse {
  files: RawFileListItem[]
}

export interface UploadingFileItem {
  taskId: string
  fileName: string
  fileType: FileType
  status: "uploading" | "failed" | "success"
  progress?: number
  size: number
  message?: string
  timestamp: string
}

export interface FileUploadListResponse {
  uploads: UploadingFileItem[]
}

const createAuthHeaders = async (extra: HeadersInit = {}) => {
  const token = await getToken()

  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra
  }
}

const authFetchWithRefresh = async (
  url: string,
  init: RequestInit = {}
): Promise<Response> => {
  await ensureFreshAccessToken()

  const firstHeaders = await createAuthHeaders(init.headers || {})
  let response = await fetch(url, {
    ...init,
    headers: firstHeaders
  })

  if (response.status === 401) {
    try {
      await refreshToken()
    } catch {
      return response
    }

    const retryHeaders = await createAuthHeaders(init.headers || {})
    response = await fetch(url, {
      ...init,
      headers: retryHeaders
    })
  }

  return response
}

export const uploadFile = async (
  file: File,
  type: FileType
): Promise<UploadFileResponse> => {
  const token = await getToken()

  const formData = new FormData()
  formData.append("file", file)

  const response = await authFetchWithRefresh(
    `${API_BASE_URL}/api/v1/files/uploads?type=${type}`,
    {
      method: "POST",
      body: formData
    }
  )

  if (!response.ok) {
    try {
      const errorData = await response.json()
      const message =
        (errorData as any)?.message ||
        (errorData as any)?.error ||
        "파일 업로드에 실패했습니다."
      throw new Error(message)
    } catch {
      throw new Error("파일 업로드에 실패했습니다.")
    }
  }

  const contentType = response.headers.get("Content-Type") || ""

  if (contentType.includes("application/json")) {
    const data = (await response.json()) as UploadFileResponse
    return data
  }

  const taskId = (await response.text()).trim()

  const fallback: UploadFileResponse = {
    taskId,
    fileName: file.name,
    fileType: type,
    status: "uploading",
    progress: 0,
    message: undefined,
    timestamp: new Date().toISOString()
  }

  return fallback
}

export const cancelUpload = async (taskId: string): Promise<void> => {
  const response = await authFetchWithRefresh(
    `${API_BASE_URL}/api/v1/files/uploads/${taskId}`,
    {
      method: "DELETE"
    }
  )

  if (!response.ok) {
    throw new Error("업로드 취소에 실패했습니다.")
  }
}

export const getFiles = async (type?: FileType): Promise<FileListItem[]> => {
  const headers = await createAuthHeaders()

  const url = new URL(`${API_BASE_URL}/api/v1/files`)
  if (type) {
    url.searchParams.set("type", type.toUpperCase())
  }

  try {
    const response = await authFetchWithRefresh(url.toString(), {
      method: "GET",
      headers
    })

    if (!response.ok) {
      if (response.status === 403) {
        const token = await getToken()
        if (!token) {
          throw new Error(
            "로그인이 필요합니다. 로그인 후 다시 시도해주세요."
          )
        }
        throw new Error(
          "접근 권한이 없습니다. 백엔드 API가 구현되었는지 확인하거나, 다시 로그인해주세요."
        )
      }
      if (response.status === 401) {
        throw new Error("인증이 만료되었습니다. 다시 로그인해주세요.")
      }

      try {
        const errorData = await response.json()
        const message =
          (errorData as any)?.message ||
          (errorData as any)?.error ||
          "파일 목록을 불러오는데 실패했습니다."
        throw new Error(message)
      } catch {
        throw new Error(
          `파일 목록을 불러오는데 실패했습니다. (상태 코드: ${response.status})`
        )
      }
    }

    const data = (await response.json()) as FileListResponse

    const mapped: FileListItem[] = data.files.map((file) => {
      const rawType = (file.fileType || "").toString().toLowerCase()
      const normalizedType: FileType = rawType === "video" ? "video" : "image"

      return {
        taskId: file.taskId,
        fileName: file.fileName,
        fileType: normalizedType,
        size: file.size,
        url: file.url,
        timestamp: file.timestamp,
        previewUrl: file.url
      }
    })

    return mapped
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(
        "네트워크 연결에 실패했습니다. 서버가 실행 중인지 확인해주세요."
      )
    }
    throw error
  }
}

export const downloadFile = async (
  taskId: string,
  fileName: string
): Promise<void> => {
  const response = await authFetchWithRefresh(
    `${API_BASE_URL}/api/v1/files/${taskId}/download`,
    {
      method: "GET"
    }
  )

  if (!response.ok) {
    throw new Error("파일 다운로드에 실패했습니다.")
  }

  const data = (await response.json()) as {
    downloadUrl: string
  }

  if (!data.downloadUrl) {
    throw new Error("다운로드 URL이 존재하지 않습니다.")
  }

  const a = document.createElement("a")
  a.href = data.downloadUrl
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

export const deleteFile = async (taskId: string): Promise<void> => {
  const response = await authFetchWithRefresh(
    `${API_BASE_URL}/api/v1/files/${taskId}`,
    {
      method: "DELETE"
    }
  )

  if (!response.ok) {
    throw new Error("파일 삭제에 실패했습니다.")
  }
}

export const getUploadingFiles = async (): Promise<UploadingFileItem[]> => {
  const response = await authFetchWithRefresh(
    `${API_BASE_URL}/api/v1/files/uploads`,
    {
      method: "GET"
    }
  )

  if (!response.ok) {
    throw new Error("업로드 중인 파일 목록을 불러오는데 실패했습니다.")
  }

  const data = (await response.json()) as FileUploadListResponse
  return data.uploads
}


