const TOKEN_KEY = "auth_token"
const REFRESH_TOKEN_KEY = "refresh_token"
const ACCESS_EXPIRES_KEY = "access_expires_at"
const REFRESH_EXPIRES_KEY = "refresh_expires_at"

const isChromeStorageAvailable =
  typeof chrome !== "undefined" &&
  !!chrome.storage &&
  !!chrome.storage.local

export const saveToken = async (token: string) => {
  if (isChromeStorageAvailable) {
    await chrome.storage.local.set({ [TOKEN_KEY]: token })
    return
  }

  // 개발 환경용 폴백
  if (typeof window !== "undefined") {
    window.localStorage.setItem(TOKEN_KEY, token)
  }
}

export const getToken = async (): Promise<string | null> => {
  let token: string | null = null

  if (isChromeStorageAvailable) {
    const result = await chrome.storage.local.get(TOKEN_KEY)
    token = (result && (result[TOKEN_KEY] as string)) || null
  } else if (typeof window !== "undefined") {
    token = window.localStorage.getItem(TOKEN_KEY)
  }

  if (token) {
    token = token.trim().replace(/\s+/g, "").replace(/,/g, "")
  }

  return token
}

export const saveRefreshToken = async (token: string) => {
  if (isChromeStorageAvailable) {
    await chrome.storage.local.set({ [REFRESH_TOKEN_KEY]: token })
    return
  }

  if (typeof window !== "undefined") {
    window.localStorage.setItem(REFRESH_TOKEN_KEY, token)
  }
}

export const getRefreshToken = async (): Promise<string | null> => {
  let token: string | null = null

  if (isChromeStorageAvailable) {
    const result = await chrome.storage.local.get(REFRESH_TOKEN_KEY)
    token = (result && (result[REFRESH_TOKEN_KEY] as string)) || null
  } else if (typeof window !== "undefined") {
    token = window.localStorage.getItem(REFRESH_TOKEN_KEY)
  }

  if (token) {
    token = token.trim().replace(/\s+/g, "").replace(/,/g, "")
  }

  return token
}

export const clearToken = async () => {
  if (isChromeStorageAvailable) {
    await chrome.storage.local.remove([
      TOKEN_KEY,
      REFRESH_TOKEN_KEY,
      ACCESS_EXPIRES_KEY,
      REFRESH_EXPIRES_KEY
    ])
    return
  }

  if (typeof window !== "undefined") {
    window.localStorage.removeItem(TOKEN_KEY)
    window.localStorage.removeItem(REFRESH_TOKEN_KEY)
    window.localStorage.removeItem(ACCESS_EXPIRES_KEY)
    window.localStorage.removeItem(REFRESH_EXPIRES_KEY)
  }
}

export const saveAccessTokenExpiry = async (isoString: string) => {
  if (!isoString) return

  if (isChromeStorageAvailable) {
    await chrome.storage.local.set({ [ACCESS_EXPIRES_KEY]: isoString })
    return
  }

  if (typeof window !== "undefined") {
    window.localStorage.setItem(ACCESS_EXPIRES_KEY, isoString)
  }
}

export const getAccessTokenExpiry = async (): Promise<string | null> => {
  if (isChromeStorageAvailable) {
    const result = await chrome.storage.local.get(ACCESS_EXPIRES_KEY)
    return (result && (result[ACCESS_EXPIRES_KEY] as string)) || null
  }

  if (typeof window !== "undefined") {
    return window.localStorage.getItem(ACCESS_EXPIRES_KEY)
  }

  return null
}

export const saveRefreshTokenExpiry = async (isoString: string) => {
  if (!isoString) return

  if (isChromeStorageAvailable) {
    await chrome.storage.local.set({ [REFRESH_EXPIRES_KEY]: isoString })
    return
  }

  if (typeof window !== "undefined") {
    window.localStorage.setItem(REFRESH_EXPIRES_KEY, isoString)
  }
}

export const getRefreshTokenExpiry = async (): Promise<string | null> => {
  if (isChromeStorageAvailable) {
    const result = await chrome.storage.local.get(REFRESH_EXPIRES_KEY)
    return (result && (result[REFRESH_EXPIRES_KEY] as string)) || null
  }

  if (typeof window !== "undefined") {
    return window.localStorage.getItem(REFRESH_EXPIRES_KEY)
  }

  return null
}


