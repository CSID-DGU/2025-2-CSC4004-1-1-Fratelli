import {
  clearToken,
  getToken,
  getRefreshToken,
  saveToken,
  saveRefreshToken,
  saveAccessTokenExpiry,
  saveRefreshTokenExpiry,
  getAccessTokenExpiry,
  getRefreshTokenExpiry
} from "../../utils/storage"

const API_BASE_URL =
  process.env.PLASMO_PUBLIC_API_BASE_URL || "https://your-api.example.com"

interface RegisterRequest {
  email: string
  password: string
}

interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  refreshToken: string
  accessTokenExpiresAt: string
  refreshTokenExpiresAt: string
}

interface RefreshTokenRequest {
  refreshToken: string
}

export interface UserInfoResponse {
  email: string
}

interface PasswordResetRequest {
  email: string
}

export const register = async (
  email: string,
  password: string
): Promise<void> => {
  const payload: RegisterRequest = { email, password }

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    try {
      const errorData = await response.json()
      const message =
        errorData?.message ||
        errorData?.error ||
        "회원가입 요청에 실패했습니다."
      throw new Error(message)
    } catch {
      throw new Error("회원가입 요청에 실패했습니다.")
    }
  }

  return
}

export const getUser = async (): Promise<UserInfoResponse> => {
  await ensureFreshAccessToken()

  const makeRequest = async () => {
    const token = await getToken()

    if (!token) {
      throw new Error("로그인이 필요합니다.")
    }

    console.log("[getUser] 요청 URL:", `${API_BASE_URL}/api/v1/auth/user`)
    console.log("[getUser] 토큰 존재:", !!token)
    console.log("[getUser] 토큰 앞부분:", token.substring(0, 50) + "...")

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/user`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      }
    })

    console.log("[getUser] 응답 상태:", response.status)
    console.log("[getUser] 응답 헤더:", Object.fromEntries(response.headers.entries()))

    return response
  }

  let response = await makeRequest()

  // 403 에러는 백엔드 JWT 필터 문제일 가능성이 높음 - 토큰 갱신 시도하지 않음
  if (response.status === 403) {
    console.error("[getUser] 403 Forbidden - 백엔드 JWT 필터가 /api/v1/auth/user를 검증하려고 시도하는 것 같습니다.")
    console.error("[getUser] 백엔드 JWT 필터에서 /api/v1/auth/** 경로를 스킵하도록 수정이 필요합니다.")
    throw new Error("백엔드 권한 설정 문제입니다. 백엔드 개발자에게 문의하세요.")
  }

  // 401 에러만 토큰 갱신 시도
  if (response.status === 401) {
    try {
      // 토큰 갱신 시도
      await refreshToken()
      response = await makeRequest()
      
      // 갱신 후에도 여전히 401이면 로그인 필요
      if (response.status === 401) {
        throw new Error("인증이 만료되었습니다. 다시 로그인해주세요.")
      }
    } catch (error) {
      // refreshToken 실패 또는 갱신 후에도 실패
      if (error instanceof Error) {
        throw error
      }
      throw new Error("인증이 만료되었습니다. 다시 로그인해주세요.")
    }
  }

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error("접근 권한이 없습니다. 다시 로그인해주세요.")
    }
    if (response.status === 401) {
      throw new Error("인증이 만료되었습니다. 다시 로그인해주세요.")
    }
    throw new Error("사용자 정보를 불러오는데 실패했습니다.")
  }

  const data = (await response.json()) as UserInfoResponse
  return data
}

export const sendPasswordResetEmail = async (email: string): Promise<void> => {
  const payload: PasswordResetRequest = { email }

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/password-reset`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    try {
      const errorData = await response.json()
      const message =
        errorData?.message ||
        errorData?.error ||
        "비밀번호 재설정 이메일 발송에 실패했습니다."
      throw new Error(message)
    } catch {
      throw new Error("비밀번호 재설정 이메일 발송에 실패했습니다.")
    }
  }
}

export const login = async (
  email: string,
  password: string
): Promise<void> => {
  const payload: LoginRequest = { email, password }

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    try {
      const errorData = await response.json()
      const message =
        errorData?.message || errorData?.error || "로그인 요청에 실패했습니다."
      throw new Error(message)
    } catch {
      throw new Error("로그인 요청에 실패했습니다.")
    }
  }

  const data = (await response.json()) as LoginResponse

  console.log("[login] 백엔드 응답 데이터:", data)
  console.log("[login] accessToken 원본:", data.accessToken)
  console.log("[login] accessToken 타입:", typeof data.accessToken)
  console.log("[login] accessToken 길이:", data.accessToken?.length)

  if (data.accessToken) {
    const cleanToken = data.accessToken.trim().replace(/\s+/g, "").replace(/,/g, "")
    console.log("[login] 정리된 토큰:", cleanToken.substring(0, 50) + "...")
    await saveToken(cleanToken)
    if (data.accessTokenExpiresAt) {
      await saveAccessTokenExpiry(data.accessTokenExpiresAt)
    }
  }

  if (data.refreshToken) {
    const cleanRefreshToken = data.refreshToken.trim().replace(/\s+/g, "").replace(/,/g, "")
    await saveRefreshToken(cleanRefreshToken)
    if (data.refreshTokenExpiresAt) {
      await saveRefreshTokenExpiry(data.refreshTokenExpiresAt)
    }
  }

  return
}

export const refreshToken = async (): Promise<void> => {
  const refreshTokenValue = await getRefreshToken()

  if (!refreshTokenValue) {
    throw new Error("리프레시 토큰이 없습니다. 다시 로그인해주세요.")
  }

  const payload: RefreshTokenRequest = {
    refreshToken: refreshTokenValue
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${refreshTokenValue}`
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    if (response.status === 403) {
      console.error("[refreshToken] 403 Forbidden - 백엔드 JWT 필터가 /api/v1/auth/refresh를 검증하려고 시도하는 것 같습니다.")
      throw new Error("토큰 재발급 권한이 없습니다. 다시 로그인해주세요.")
    }
    try {
      const errorData = await response.json()
      const message =
        errorData?.message ||
        errorData?.error ||
        "토큰 재발급 요청에 실패했습니다."
      throw new Error(message)
    } catch {
      throw new Error("토큰 재발급 요청에 실패했습니다.")
    }
  }

  const data = (await response.json()) as LoginResponse

  if (data.accessToken) {
    const cleanToken = data.accessToken.trim().replace(/\s+/g, "").replace(/,/g, "")
    await saveToken(cleanToken)
    if (data.accessTokenExpiresAt) {
      await saveAccessTokenExpiry(data.accessTokenExpiresAt)
    }
  }

  if (data.refreshToken) {
    const cleanRefreshToken = data.refreshToken.trim().replace(/\s+/g, "").replace(/,/g, "")
    await saveRefreshToken(cleanRefreshToken)
    if (data.refreshTokenExpiresAt) {
      await saveRefreshTokenExpiry(data.refreshTokenExpiresAt)
    }
  }
}

const ACCESS_TOKEN_SKEW_MS = 60 * 1000 

export const ensureFreshAccessToken = async (): Promise<void> => {
  const accessExp = await getAccessTokenExpiry()
  const refreshExp = await getRefreshTokenExpiry()

  if (!accessExp) {
    return
  }

  const now = Date.now()
  const accessExpTime = Date.parse(accessExp)

  if (Number.isNaN(accessExpTime)) {
    return
  }

  if (refreshExp) {
    const refreshExpTime = Date.parse(refreshExp)
    if (!Number.isNaN(refreshExpTime) && now >= refreshExpTime) {
      return
    }
  }

  if (now < accessExpTime - ACCESS_TOKEN_SKEW_MS) {
    return
  }

  try {
    await refreshToken()
  } catch (e) {
    console.error("액세스 토큰 사전 갱신 실패:", e)
  }
}

export const logout = async () => {
  try {
    const makeRequest = async () => {
      const token = await getToken()
      return await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      })
    }

    let response = await makeRequest()

    if (response.status === 401) {
      try {
        await refreshToken()
        response = await makeRequest()
      } catch {
        await clearToken()
        return
      }
    }

    if (!response.ok) {
      try {
        const errorData = await response.json()
        const message =
          errorData?.message ||
          errorData?.error ||
          "로그아웃 요청에 실패했습니다."
        throw new Error(message)
      } catch {
        throw new Error("로그아웃 요청에 실패했습니다.")
      }
    }
  } finally {
    await clearToken()
  }
}

export const quit = async () => {
  await ensureFreshAccessToken()

  const performRequest = async () => {
    const token = await getToken()

    if (!token) {
      throw new Error("로그인이 필요합니다.")
    }

    return await fetch(`${API_BASE_URL}/api/v1/auth/quit`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      }
    })
  }

  try {
    let response = await performRequest()

    console.log("[quit] 응답 상태:", response.status)

    // 403 에러는 백엔드 JWT 필터 문제일 가능성이 높음
    if (response.status === 403) {
      console.error("[quit] 403 Forbidden - 백엔드 JWT 필터가 /api/v1/auth/quit를 검증하려고 시도하는 것 같습니다.")
      throw new Error("회원탈퇴 권한이 없습니다. 백엔드 설정을 확인해주세요.")
    }

    if (response.status === 401) {
      try {
        await refreshToken()
        response = await performRequest()
        console.log("[quit] 토큰 갱신 후 응답 상태:", response.status)
      } catch {
        await clearToken()
        throw new Error("인증이 만료되었습니다. 다시 로그인해주세요.")
      }
    }

    // 응답 상태 확인
    if (!response.ok) {
      // 실패 시 토큰 유지 (회원탈퇴 실패했으므로)
      try {
        const errorData = await response.json()
        const message =
          errorData?.message ||
          errorData?.error ||
          `회원탈퇴에 실패했습니다. (상태 코드: ${response.status})`
        throw new Error(message)
      } catch {
        throw new Error(`회원탈퇴에 실패했습니다. (상태 코드: ${response.status})`)
      }
    }

    console.log("[quit] 회원탈퇴 성공")
    // 성공한 경우에만 토큰 삭제
    await clearToken()
    return
  } catch (error) {
    throw error
  }
}


