import { useState, useRef, useEffect } from "react"

import { VscAccount } from "react-icons/vsc"

interface UserInfoProps {
  isLoggedIn: boolean
  userEmail?: string
  onLoginClick?: () => void
  onSignUpClick?: () => void
  onLogoutClick?: () => void
  onDeleteAccountClick?: () => void
}

const UserInfo = ({
  isLoggedIn,
  userEmail,
  onLoginClick,
  onSignUpClick,
  onLogoutClick,
  onDeleteAccountClick
}: UserInfoProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isOpen])

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  return (
    <div
      ref={dropdownRef}
      style={{
        position: "relative",
        display: "inline-block"
      }}>
      <button
        onClick={handleToggle}
        style={{
          width: 32,
          height: 32,
          border: "none",
          backgroundColor: "transparent",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 0,
          outline: "none"
        }}>
        <VscAccount
          style={{
            color: "rgba(39, 0, 93, 1)",
            fontSize: 20
          }}
        />
      </button>

      {isOpen && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            right: 0,
            marginTop: 0,
            backgroundColor: "white",
            borderRadius: 8,
            border: "1px solid rgba(39, 0, 93, 1)",
            boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.15)",
            minWidth: isLoggedIn ? 180 : 120,
            zIndex: 1000,
            overflow: "hidden"
          }}>
          {isLoggedIn ? (
            <>
              <div
                style={{
                  padding: "8px 12px",
                  borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                  color: "rgba(29, 5, 35, 1)",
                  fontSize: 14,
                  fontFamily: "'K2D', sans-serif"
                }}>
                {userEmail || "email@example.com"}
              </div>
              <button
                onClick={() => {
                  onLogoutClick?.()
                  setIsOpen(false)
                }}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "none",
                  borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  textAlign: "left",
                  color: "rgba(29, 5, 35, 1)",
                  fontSize: 14,
                  fontFamily: "'K2D', sans-serif",
                  transition: "background-color 0.2s ease"
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "rgba(0, 0, 0, 0.05)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent"
                }}>
                로그아웃
              </button>
              <button
                onClick={() => {
                  onDeleteAccountClick?.()
                  setIsOpen(false)
                }}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  textAlign: "left",
                  color: "rgba(29, 5, 35, 1)",
                  fontSize: 14,
                  fontFamily: "'K2D', sans-serif",
                  transition: "background-color 0.2s ease"
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "rgba(0, 0, 0, 0.05)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent"
                }}>
                회원 탈퇴
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => {
                  onLoginClick?.()
                  setIsOpen(false)
                }}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "none",
                  borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  textAlign: "left",
                  color: "rgba(29, 5, 35, 1)",
                  fontSize: 14,
                  fontFamily: "'K2D', sans-serif",
                  transition: "background-color 0.2s ease"
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "rgba(0, 0, 0, 0.05)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent"
                }}>
                로그인
              </button>
              <button
                onClick={() => {
                  onSignUpClick?.()
                  setIsOpen(false)
                }}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  textAlign: "left",
                  color: "rgba(29, 5, 35, 1)",
                  fontSize: 14,
                  fontFamily: "'K2D', sans-serif",
                  transition: "background-color 0.2s ease"
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "rgba(0, 0, 0, 0.05)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent"
                }}>
                회원가입
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default UserInfo

