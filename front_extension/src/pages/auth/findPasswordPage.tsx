import { useState } from "react"

import { SlArrowLeft, SlEnvolope } from "react-icons/sl"

import FullFormInput from "../../components/auth/fullFormInput"
import LoginButton from "../../components/auth/logInButton"
import { sendPasswordResetEmail } from "../../services/auth/auth.services"

interface FindPasswordPageProps {
  onBack?: () => void
  onLoginClick?: () => void
}

const FindPasswordPage = ({ onBack, onLoginClick }: FindPasswordPageProps) => {
  const [email, setEmail] = useState("")
  const [showModal, setShowModal] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSendPasswordResetEmail = async () => {
    const trimmedEmail = email.trim()

    if (trimmedEmail === "") {
      alert("이메일을 입력해주세요.")
      return
    }

    setIsLoading(true)

    try {
      await sendPasswordResetEmail(trimmedEmail)
      setShowModal(true)
    } catch (e) {
      alert(
        `이메일 발송에 실패했습니다: ${
          e instanceof Error ? e.message : "알 수 없는 오류"
        }`
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirm = () => {
    setShowModal(false)
    onLoginClick?.()
  }

  return (
    <>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          backgroundColor: "white",
          overflowY: "auto"
        }}>
        {onBack && (
          <div
            style={{
              padding: "15px 10px",
              display: "flex",
              alignItems: "center"
            }}>
            <button
              onClick={onBack}
              style={{
                border: "none",
                backgroundColor: "transparent",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: 4,
                outline: "none"
              }}>
              <SlArrowLeft
                style={{
                  color: "black",
                  fontSize: 16
                }}
              />
            </button>
          </div>
        )}

        <div
          style={{
            padding: "40px 30px 40px 30px",
            display: "flex",
            flexDirection: "column",
            gap: 4
          }}>
          <h1
            style={{
              fontSize: 24,
              fontFamily: "'K2D', sans-serif",
              fontWeight: 600,
              color: "black",
              margin: 0
            }}>
            비밀번호 찾기
          </h1>
          <p
            style={{
              fontSize: 13,
              fontFamily: "'K2D', sans-serif",
              color: "rgba(136, 86, 204, 1)",
              margin: 0
            }}>
            가입하신 이메일을 입력해주세요.
            <br />
            비밀번호 재설정 이메일을 보내드립니다.
          </p>
        </div>

        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: "0 8px",
            paddingTop: 0
          }}>
          <FullFormInput
            text="Email"
            text2="이메일을 입력하세요."
            value={email}
            onChange={setEmail}
            prefixIcon={
              <SlEnvolope
                style={{
                  color: "rgba(39, 0, 93, 1)",
                  fontSize: 20
                }}
              />
            }
          />

          <div style={{ height: 56 }} />

          <LoginButton
            text={isLoading ? "발송 중..." : "이메일 발송"}
            onTap={isLoading ? undefined : handleSendPasswordResetEmail}
          />
        </div>
      </div>

      {showModal && (
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
          onClick={() => setShowModal(false)}>
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
              이메일 발송 완료
            </h2>

            <p
              style={{
                fontSize: 14,
                fontFamily: "'K2D', sans-serif",
                color: "rgba(29, 5, 35, 1)",
                margin: "0 0 24px 0",
                lineHeight: 1.5
              }}>
              비밀번호 재설정 이메일을 발송했습니다.
              <br />
              이메일을 확인해주세요.
            </p>

            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: 8
              }}>
              <button
                onClick={handleConfirm}
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

export default FindPasswordPage

