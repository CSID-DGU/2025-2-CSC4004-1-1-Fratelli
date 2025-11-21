import { useState } from "react"

import { SlArrowLeft, SlEnvolope, SlLock } from "react-icons/sl"

import FullFormInput from "../../components/auth/fullFormInput"
import LoginButton from "../../components/auth/logInButton"
import TextButton from "../../components/auth/textButton"
import { login } from "../../services/auth/auth.services"

interface LogInPageProps {
  onBack?: () => void
  onSignUpClick?: () => void
  onFindPasswordClick?: () => void
  onLoginSuccess?: (email: string) => void
}

const LogInPage = ({
  onBack,
  onSignUpClick,
  onFindPasswordClick,
  onLoginSuccess
}: LogInPageProps) => {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLogin = async () => {
    if (!email || !password) {
      setError("이메일과 비밀번호를 입력해주세요.")
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      await login(email.trim(), password)

      onLoginSuccess?.(email.trim())
      setIsLoading(false)
    } catch (err) {
      setIsLoading(false)
      setError(err instanceof Error ? err.message : "로그인에 실패했습니다.")
    }
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        backgroundColor: "white",
        overflow: "auto"
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
          로그인
        </h1>
        <p
          style={{
            fontSize: 15,
            fontFamily: "'K2D', sans-serif",
            color: "rgba(136, 86, 204, 1)",
            margin: 0
          }}>
          Lets login to use Deepflect
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

        <div style={{ height: 36 }} />

        <FullFormInput
          text="Password"
          text2="비밀번호를 입력하세요."
          isPassword={true}
          value={password}
          onChange={setPassword}
          prefixIcon={
            <SlLock
              style={{
                color: "rgba(39, 0, 93, 1)",
                fontSize: 20
              }}
            />
          }
        />

        <div style={{ height: 30 }} />

        <div
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "flex-end",
            paddingRight: "36px"
          }}>
          <TextButton
            text="비밀번호 찾기"
            fontSize={13}
            onTap={() => onFindPasswordClick?.()}
          />
        </div>

        <div style={{ height: 55 }} />

        {error && (
          <div
            style={{
              width: "100%",
              padding: "12px",
              marginBottom: 16,
              backgroundColor: "#ffebee",
              color: "#c62828",
              borderRadius: 8,
              fontSize: 14,
              fontFamily: "'K2D', sans-serif",
              textAlign: "center"
            }}>
            {error}
          </div>
        )}

        {isLoading ? (
          <div
            style={{
              width: "100%",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: 60
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
        ) : (
          <LoginButton text="로그인" onTap={handleLogin} />
        )}

        <div style={{ height: 16 }} />

        <TextButton text="회원가입" fontSize={13} onTap={() => onSignUpClick?.()} />
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

export default LogInPage

