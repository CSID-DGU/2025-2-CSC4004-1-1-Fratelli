interface TextButtonProps {
  text: string
  onTap: () => void
  fontSize?: number
}

const TextButton = ({ text, onTap, fontSize = 17 }: TextButtonProps) => {
  return (
    <div
      onClick={onTap}
      style={{
        cursor: "pointer",
        backgroundColor: "rgba(148, 0, 255, 0)",
        padding: 2,
        display: "inline-block"
      }}>
      <span
        style={{
          color: "rgba(136, 86, 204, 1)",
          fontSize: fontSize,
          fontWeight: 500,
          lineHeight: "0.08",
          fontFamily: "'K2D', sans-serif",
          textAlign: "center",
          display: "block"
        }}>
        {text}
      </span>
    </div>
  )
}

export default TextButton

