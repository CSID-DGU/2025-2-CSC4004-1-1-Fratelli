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

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/user`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      }
    })

    return response
  }

  let response = await makeRequest()

  if (response.status === 401) {
    try {
      await refreshToken()
      response = await makeRequest()
    } catch {
      throw new Error("인증이 만료되었습니다. 다시 로그인해주세요.")
    }
  }

  if (!response.ok) {
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
  try {
    const makeRequest = async () => {
      const token = await getToken()
      return await fetch(`${API_BASE_URL}/api/v1/auth/quit`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
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
  } finally {
    await clearToken()
  }
}


