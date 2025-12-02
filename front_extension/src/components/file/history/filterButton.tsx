interface FilterButtonProps {
  title: string
  onTap: () => void
  isSelected: boolean
}

const FilterButton = ({ title, onTap, isSelected }: FilterButtonProps) => {
  const borderColor = "rgba(39, 0, 93, 1)"

  return (
    <div
      onClick={onTap}
      style={{
        cursor: "pointer",
        padding: "6px 4px",
        backgroundColor: isSelected ? borderColor : "white",
        border: `1px solid ${borderColor}`,
        borderRadius: 8,
        boxShadow: isSelected
          ? "4px 10px 20px -10px rgba(0, 0, 0, 0.33)"
          : "none",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        boxSizing: "border-box"
      }}>
      <span
        style={{
          color: isSelected ? "white" : borderColor,
          fontWeight: "bold",
          fontSize: 12,
          textAlign: "center"
        }}>
        {title}
      </span>
    </div>
  )
}

export default FilterButton

