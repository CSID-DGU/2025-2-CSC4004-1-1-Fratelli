import { useState } from "react"

import { SlArrowLeft, SlEnvolope, SlLock } from "react-icons/sl"

import { register } from "../../services/auth/auth.services"

import FullFormInput from "../../components/auth/fullFormInput"
import LoginButton from "../../components/auth/logInButton"

interface SignUpPageProps {
  onBack?: () => void
  onLoginClick?: () => void
  onSignUpSuccess?: () => void
}

const SignUpPage = ({
  onBack,
  onLoginClick,
  onSignUpSuccess
}: SignUpPageProps) => {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateEmail = (value: string): string | undefined => {
    if (!value || value.trim() === "") {
      return "이메일을 입력해주세요."
    }
    if (!value.includes("@") || !value.includes(".")) {
      return "올바른 이메일 형식을 입력해주세요."
    }
    return undefined
  }

  const validatePassword = (value: string): string | undefined => {
    if (!value || value.trim() === "") {
      return "비밀번호를 입력해주세요."
    }
    if (value.length < 6) {
      return "비밀번호는 최소 6자 이상이어야 합니다."
    }
    return undefined
  }

  const validateConfirmPassword = (value: string): string | undefined => {
    if (!value || value.trim() === "") {
      return "비밀번호 확인을 입력해주세요."
    }
    if (value !== password) {
      return "비밀번호가 일치하지 않습니다."
    }
    return undefined
  }

  const handleSignUp = async () => {
    const emailError = validateEmail(email)
    const passwordError = validatePassword(password)
    const confirmPasswordError = validateConfirmPassword(confirmPassword)

    const firstError =
      emailError || passwordError || confirmPasswordError || null

    if (firstError) {
      setError(firstError)
      return
    }

    if (password !== confirmPassword) {
      setError("비밀번호가 일치하지 않습니다.")
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      await register(email.trim(), password)

      setIsLoading(false)
      onSignUpSuccess?.()
      onLoginClick?.()
    } catch (err) {
      setIsLoading(false)
      setError(
        err instanceof Error
          ? err.message.replace("Exception: ", "")
          : "회원가입에 실패했습니다."
      )
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
            disabled={isLoading}
            style={{
              border: "none",
              backgroundColor: "transparent",
              cursor: isLoading ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: 4,
              outline: "none",
              opacity: isLoading ? 0.5 : 1
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
          회원가입
        </h1>
        <p
          style={{
            fontSize: 15,
            fontFamily: "'K2D', sans-serif",
            color: "rgba(136, 86, 204, 1)",
            margin: 0
          }}>
          Create account to use Deepflect
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
          validator={validateEmail}
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
          text2="비밀번호를 입력하세요"
          isPassword={true}
          value={password}
          onChange={setPassword}
          validator={validatePassword}
          prefixIcon={
            <SlLock
              style={{
                color: "rgba(39, 0, 93, 1)",
                fontSize: 20
              }}
            />
          }
        />

        <div style={{ height: 36 }} />

        <FullFormInput
          text="Password 확인"
          text2="비밀번호를 입력하세요."
          isPassword={true}
          value={confirmPassword}
          onChange={setConfirmPassword}
          validator={validateConfirmPassword}
          prefixIcon={
            <SlLock
              style={{
                color: "rgba(39, 0, 93, 1)",
                fontSize: 20
              }}
            />
          }
        />

        {error && (
          <div
            style={{
              width: "100%",
              padding: "12px",
              marginTop: 16,
              backgroundColor: "#ffebee",
              border: "1px solid #ef5350",
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              gap: 8
            }}>
            <span
              style={{
                fontSize: 20,
                color: "#c62828"
              }}>
              ⚠️
            </span>
            <span
              style={{
                color: "#c62828",
                fontSize: 14,
                fontFamily: "'K2D', sans-serif",
                flex: 1
              }}>
              {error}
            </span>
          </div>
        )}

        <div style={{ height: 50 }} />

        {isLoading ? (
          <div
            style={{
              width: "100%",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: 42
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
          <LoginButton
            text="회원가입"
            onTap={handleSignUp}
          />
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

export default SignUpPage

