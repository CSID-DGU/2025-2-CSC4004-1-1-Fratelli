import UserInfo from "../auth/userInfo"

interface CustomNavigationBarProps {
  activeTab: "upload" | "history"
  onTabChange: (tab: "upload" | "history") => void
  isLoggedIn?: boolean
  userEmail?: string
  onLoginClick?: () => void
  onSignUpClick?: () => void
  onLogoutClick?: () => void
  onDeleteAccountClick?: () => void
}

const CustomNavigationBar = ({
  activeTab,
  onTabChange,
  isLoggedIn = false,
  userEmail,
  onLoginClick,
  onSignUpClick,
  onLogoutClick,
  onDeleteAccountClick
}: CustomNavigationBarProps) => {
  const tabs = [
    { id: "upload" as const, label: "Upload" },
    { id: "history" as const, label: "History" }
  ]

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        backgroundColor: "white",
        borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
        padding: "8px 16px"
      }}>
      <div
        style={{
          display: "flex",
          gap: 0,
          flex: 1
        }}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              style={{
                padding: "6px 12px",
                border: "none",
                backgroundColor: "transparent",
                cursor: "pointer",
                position: "relative",
                outline: "none"
              }}>
              {/* 텍스트 */}
              <span
                style={{
                  color: isActive
                    ? "rgba(29, 5, 35, 1)"
                    : "rgba(128, 128, 128, 1)",
                  fontSize: 16,
                  fontFamily: "'K2D', sans-serif",
                  fontWeight: isActive ? 600 : 400,
                  transition: "color 0.2s ease"
                }}>
                {tab.label}
              </span>

              {isActive && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: 2,
                    backgroundColor: "rgba(29, 5, 35, 1)",
                    borderRadius: "2px 2px 0 0"
                  }}
                />
              )}
            </button>
          )
        })}
      </div>

      <div style={{ marginLeft: 16 }}>
        <UserInfo
          isLoggedIn={isLoggedIn}
          userEmail={userEmail}
          onLoginClick={onLoginClick}
          onSignUpClick={onSignUpClick}
          onLogoutClick={onLogoutClick}
          onDeleteAccountClick={onDeleteAccountClick}
        />
      </div>
    </div>
  )
}

export default CustomNavigationBar

