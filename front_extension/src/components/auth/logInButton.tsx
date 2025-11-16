import type { ReactNode } from "react"

interface LoginButtonProps {
  text: string
  onTap?: () => void
  icon?: ReactNode
}

const LoginButton = ({ text, onTap, icon }: LoginButtonProps) => {
  // 사이드 패널의 부모 컨테이너 너비에서 양쪽 여백(24px * 2)을 뺀 크기
  const horizontalPadding = 24.0

  return (
    <div
      onClick={onTap}
      style={{
        cursor: onTap ? "pointer" : "default",
        width: `calc(100% - ${horizontalPadding * 2}px)`,
        height: 42,
        position: "relative",
        margin: `0 ${horizontalPadding}px`,
        backgroundColor: "transparent"
      }}>
      {/* 배경 컨테이너 (그림자 포함) */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: "100%",
          height: 42,
          backgroundColor: "rgba(39, 0, 93, 1)",
          borderRadius: 12,
          boxShadow: "0px 4px 50px rgba(0, 0, 0, 0.25)",
          boxSizing: "border-box"
        }}
      />

      {/* 텍스트와 아이콘 (중앙 정렬, 약간 위로 이동) */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, calc(-50% - 2px))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8
        }}>
        {icon && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              color: "white",
              fontSize: 24
            }}>
            {icon}
          </div>
        )}
        <span
          style={{
            color: "white",
            fontSize: 16,
            fontWeight: 600,
            lineHeight: "0.99",
            fontFamily: "'K2D', sans-serif",
            textAlign: "center"
          }}>
          {text}
        </span>
      </div>
    </div>
  )
}

export default LoginButton

