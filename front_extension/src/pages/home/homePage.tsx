import { useEffect, useState } from "react"

import CustomNavigationBar from "../../components/home/customNavigationBar"
import FileUploadPage from "../file/upload/fileUploadPage"
import FileHistoryPage from "../file/history/fileHistoryPage"
import LogInPage from "../auth/logInPage"
import SignUpPage from "../auth/signUpPage"
import FindPasswordPage from "../auth/findPasswordPage"
import { getUser, logout, quit } from "../../services/auth/auth.services"

const HomePage = () => {
  const [currentTab, setCurrentTab] = useState<"upload" | "history">("upload")
  const [currentPage, setCurrentPage] = useState<"home" | "login" | "signup" | "findPassword">("home")
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userEmail, setUserEmail] = useState<string | undefined>()
  const [refreshHistory, setRefreshHistory] = useState(0)
  const [logoutVersion, setLogoutVersion] = useState(0)
  const [showLogoutModal, setShowLogoutModal] = useState(false)
  const [showDeleteAccountModal, setShowDeleteAccountModal] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      try {
        const user = await getUser()
        setIsLoggedIn(true)
        setUserEmail(user.email)
      } catch (error) {
        console.error("[HomePage] 인증 초기화 실패:", error)
        setIsLoggedIn(false)
        setUserEmail(undefined)
        // 403 에러인 경우 토큰 삭제
        if (error instanceof Error && error.message.includes("권한")) {
          // 토큰이 있지만 권한이 없는 경우, 토큰을 삭제하고 로그인 페이지로
        }
      } finally {
        setIsInitializing(false)
      }
    }

    void initAuth()
  }, [])

  const handleTabChange = (tab: "upload" | "history") => {
    setCurrentTab(tab)
  }

  const handleLoginClick = () => {
    setCurrentPage("login")
  }

  const handleSignUpClick = () => {
    setCurrentPage("signup")
  }

  const handleSignUpSuccess = () => {
    setCurrentPage("login")
  }

  const handleLogoutClick = () => {
    setShowLogoutModal(true)
  }

  const handleLogoutConfirm = async () => {
    try {
      await logout()
    } catch (e) {
      console.error("로그아웃 실패:", e)
    } finally {
      setIsLoggedIn(false)
      setUserEmail(undefined)
      setLogoutVersion((prev) => prev + 1)
      setCurrentTab("upload")
      setShowLogoutModal(false)
    }
  }

  const handleLogoutCancel = () => {
    setShowLogoutModal(false)
  }

  const handleDeleteAccountClick = () => {
    setShowDeleteAccountModal(true)
  }

  const handleDeleteAccountConfirm = async () => {
    try {
      await quit()
      alert("회원 탈퇴가 완료되었습니다.")
      // 성공한 경우에만 상태 초기화
      setIsLoggedIn(false)
      setUserEmail(undefined)
      setLogoutVersion((prev) => prev + 1)
      setCurrentTab("upload")
    } catch (e) {
      alert(
        `회원 탈퇴에 실패했습니다: ${
          e instanceof Error ? e.message : "알 수 없는 오류"
        }`
      )
      // 실패한 경우 상태 유지 (로그인 상태 유지)
    } finally {
      setShowDeleteAccountModal(false)
    }
  }

  const handleDeleteAccountCancel = () => {
    setShowDeleteAccountModal(false)
  }

  const handleLoginSuccess = (email: string) => {
    setIsLoggedIn(true)
    setUserEmail(email || "user@example.com")
    setCurrentPage("home")
  }

  const handleBack = () => {
    setCurrentPage("home")
  }

  const handleFindPasswordClick = () => {
    setCurrentPage("findPassword")
  }

  if (currentPage === "login") {
    return (
      <LogInPage
        onBack={handleBack}
        onSignUpClick={handleSignUpClick}
        onFindPasswordClick={handleFindPasswordClick}
        onLoginSuccess={handleLoginSuccess}
      />
    )
  }

  if (currentPage === "signup") {
    return (
      <SignUpPage
        onBack={handleBack}
        onLoginClick={handleLoginClick}
        onSignUpSuccess={handleSignUpSuccess}
      />
    )
  }

  if (currentPage === "findPassword") {
    return (
      <FindPasswordPage
        onBack={handleBack}
        onLoginClick={handleLoginClick}
      />
    )
  }

  return (
    <>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          backgroundColor: "white"
        }}>
        <CustomNavigationBar
          activeTab={currentTab}
          onTabChange={handleTabChange}
          isLoggedIn={isLoggedIn}
          userEmail={userEmail}
          onLoginClick={handleLoginClick}
          onSignUpClick={handleSignUpClick}
          onLogoutClick={handleLogoutClick}
          onDeleteAccountClick={handleDeleteAccountClick}
        />

        <div
          style={{
            flex: 1,
            overflow: "hidden",
            position: "relative"
          }}>
          <div
            style={{
              display: currentTab === "upload" ? "block" : "none",
              width: "100%",
              height: "100%"
            }}>
            <FileUploadPage
              onUploadSuccess={() => {
                // 업로드 성공 후 즉시 새로고침
                setRefreshHistory((prev) => prev + 1)
                // 백엔드 처리 시간을 고려하여 지연 후 추가 새로고침
                setTimeout(() => {
                  setRefreshHistory((prev) => prev + 1)
                }, 2000) // 2초 후
                setTimeout(() => {
                  setRefreshHistory((prev) => prev + 1)
                }, 5000) // 5초 후
              }}
              logoutVersion={logoutVersion}
            />
          </div>
          <div
            style={{
              display: currentTab === "history" ? "block" : "none",
              width: "100%",
              height: "100%"
            }}>
            <FileHistoryPage
              refreshTrigger={refreshHistory}
              isLoggedIn={isLoggedIn}
              logoutVersion={logoutVersion}
            />
          </div>
        </div>
      </div>

      {showLogoutModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }}
          onClick={handleLogoutCancel}>
          <div
            style={{
              backgroundColor: "white",
              borderRadius: 12,
              padding: "24px",
              width: "80%",
              maxWidth: 280,
              boxShadow: "0px 4px 20px rgba(0, 0, 0, 0.2)"
            }}
            onClick={(e) => e.stopPropagation()}>
            <h2
              style={{
                fontSize: 20,
                fontFamily: "'K2D', sans-serif",
                fontWeight: 600,
                color: "black",
                margin: "0 0 16px 0"
              }}>
              로그아웃
            </h2>

            <p
              style={{
                fontSize: 14,
                fontFamily: "'K2D', sans-serif",
                color: "rgba(29, 5, 35, 1)",
                margin: "0 0 24px 0",
                lineHeight: 1.5
              }}>
              로그아웃 하시겠습니까?
            </p>

            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: 8
              }}>
              <button
                onClick={handleLogoutCancel}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "white",
                  color: "rgba(39, 0, 93, 1)",
                  border: "1px solid rgba(39, 0, 93, 1)",
                  borderRadius: 8,
                  cursor: "pointer",
                  fontFamily: "'K2D', sans-serif",
                  fontSize: 14,
                  fontWeight: 500
                }}>
                취소
              </button>
              <button
                onClick={handleLogoutConfirm}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "rgba(39, 0, 93, 1)",
                  color: "white",
                  border: "none",
                  borderRadius: 8,
                  cursor: "pointer",
                  fontFamily: "'K2D', sans-serif",
                  fontSize: 14,
                  fontWeight: 500
                }}>
                확인
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteAccountModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }}
          onClick={handleDeleteAccountCancel}>
          <div
            style={{
              backgroundColor: "white",
              borderRadius: 12,
              padding: "24px",
              width: "80%",
              maxWidth: 280,
              boxShadow: "0px 4px 20px rgba(0, 0, 0, 0.2)"
            }}
            onClick={(e) => e.stopPropagation()}>
            {/* 제목 */}
            <h2
              style={{
                fontSize: 20,
                fontFamily: "'K2D', sans-serif",
                fontWeight: 600,
                color: "black",
                margin: "0 0 16px 0"
              }}>
              회원 탈퇴
            </h2>

            <p
              style={{
                fontSize: 14,
                fontFamily: "'K2D', sans-serif",
                color: "rgba(29, 5, 35, 1)",
                margin: "0 0 24px 0",
                lineHeight: 1.5
              }}>
              회원 탈퇴를 하시겠습니까?
              <br />
              탈퇴 시 모든 데이터가 삭제됩니다.
            </p>

            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: 8
              }}>
              <button
                onClick={handleDeleteAccountCancel}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "white",
                  color: "rgba(39, 0, 93, 1)",
                  border: "1px solid rgba(39, 0, 93, 1)",
                  borderRadius: 8,
                  cursor: "pointer",
                  fontFamily: "'K2D', sans-serif",
                  fontSize: 14,
                  fontWeight: 500
                }}>
                취소
              </button>
              <button
                onClick={handleDeleteAccountConfirm}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "rgba(39, 0, 93, 1)",
                  color: "white",
                  border: "none",
                  borderRadius: 8,
                  cursor: "pointer",
                  fontFamily: "'K2D', sans-serif",
                  fontSize: 14,
                  fontWeight: 500
                }}>
                확인
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default HomePage

