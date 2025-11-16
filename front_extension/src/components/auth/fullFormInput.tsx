import { useState, useRef } from "react"

interface FullFormInputProps {
  text: string
  text2: string
  isPassword?: boolean
  controller?: React.RefObject<HTMLInputElement>
  prefixIcon?: React.ReactNode
  validator?: (value: string) => string | undefined
  value?: string
  onChange?: (value: string) => void
}

const FullFormInput = ({
  text,
  text2,
  isPassword = false,
  controller,
  prefixIcon,
  validator,
  value: controlledValue,
  onChange
}: FullFormInputProps) => {
  const [internalValue, setInternalValue] = useState("")
  const [error, setError] = useState<string | undefined>(undefined)
  const inputRef = useRef<HTMLInputElement>(null)

  // controlled 또는 uncontrolled 모드 지원
  const isControlled = controlledValue !== undefined
  const value = isControlled ? controlledValue : internalValue

  // 사이드 패널의 부모 컨테이너 너비에서 양쪽 여백(24px * 2)을 뺀 크기
  const horizontalPadding = 24.0

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value

    if (!isControlled) {
      setInternalValue(newValue)
    }

    // 유효성 검사
    if (validator) {
      const errorMessage = validator(newValue)
      setError(errorMessage)
    } else {
      setError(undefined)
    }

    onChange?.(newValue)
  }

  const handleBlur = () => {
    if (validator && value) {
      const errorMessage = validator(value)
      setError(errorMessage)
    }
  }

  // ref 병합 (controller와 내부 ref)
  const inputRefToUse = controller || inputRef

  return (
    <div
      style={{
        width: `calc(100% - ${horizontalPadding * 2}px)`,
        height: 55,
        display: "flex",
        flexDirection: "column",
        margin: `0 ${horizontalPadding}px`
      }}>
      {/* 라벨 텍스트 */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          marginBottom: 6
        }}>
        <span
          style={{
            color: "rgba(29, 5, 35, 1)",
            fontSize: 16,
            fontWeight: 500,
            lineHeight: "1.2",
            fontFamily: "'K2D', sans-serif"
          }}>
          {text}
        </span>
      </div>

      {/* 입력 필드 */}
      <div
        style={{
          width: "100%",
          height: 42
        }}>
        <div
          style={{
            width: "100%",
            height: "100%",
            border: "1.3px solid rgba(39, 0, 93, 1)",
            borderRadius: 12,
            position: "relative",
            display: "flex",
            alignItems: "center",
            boxShadow: "none"
          }}>
          {prefixIcon && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                paddingLeft: 8
              }}>
              {prefixIcon}
            </div>
          )}
          <input
            ref={inputRefToUse}
            type={isPassword ? "password" : "text"}
            value={value}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder={text2}
            style={{
              flex: 1,
              border: "none",
              outline: "none",
              padding: "10px 14px",
              paddingLeft: prefixIcon ? "8px" : "14px",
              fontFamily: "'K2D', sans-serif",
              fontSize: 14,
              fontWeight: 500,
              color: "rgba(29, 5, 35, 1)",
              backgroundColor: "transparent"
            }}
          />
        </div>
        {error && (
          <div
            style={{
              fontSize: 12,
              color: "#c62828",
              lineHeight: 1.2,
              marginTop: 4,
              paddingLeft: 4
            }}>
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

export default FullFormInput

