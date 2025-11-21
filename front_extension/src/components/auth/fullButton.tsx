interface FullButtonProps {
  text: string
  onTap: () => void
}

const FullButton = ({ text, onTap }: FullButtonProps) => {
  const horizontalPadding = 24.0

  return (
    <div
      onClick={onTap}
      style={{
        cursor: "pointer",
        width: `calc(100% - ${horizontalPadding * 2}px)`,
        height: 55,
        position: "relative",
        margin: `0 ${horizontalPadding}px`
      }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: "100%",
          height: 55,
          border: "1.5px solid rgba(39, 0, 93, 1.0)",
          borderRadius: 15,
          boxSizing: "border-box"
        }}
      />

      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          paddingTop: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: 22
        }}>
        <span
          style={{
            color: "rgba(29, 5, 35, 1)",
            fontSize: 16,
            fontWeight: 600,
            lineHeight: "0.09",
            fontFamily: "'K2D', sans-serif",
            textAlign: "center"
          }}>
          {text}
        </span>
      </div>
    </div>
  )
}

export default FullButton

