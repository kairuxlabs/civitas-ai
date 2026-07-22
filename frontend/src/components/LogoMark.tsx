interface Props {
  size?: number
}

const NODES = [
  { cx: 16, cy: 6 },
  { cx: 6, cy: 14 },
  { cx: 26, cy: 14 },
  { cx: 11, cy: 25 },
  { cx: 21, cy: 25 },
]

const EDGES: [number, number][] = [
  [0, 1], [0, 2], [1, 3], [2, 4], [1, 4], [2, 3],
]

export default function LogoMark({ size = 24 }: Props) {
  return (
    <svg
      data-testid="logo-mark"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {EDGES.map(([a, b], i) => (
        <line
          key={i}
          x1={NODES[a].cx} y1={NODES[a].cy}
          x2={NODES[b].cx} y2={NODES[b].cy}
          stroke="currentColor"
          strokeWidth="1"
          strokeOpacity="0.5"
        />
      ))}
      {NODES.map((n, i) => (
        <circle key={i} cx={n.cx} cy={n.cy} r={i === 0 ? 3 : 2.5} fill="currentColor" />
      ))}
    </svg>
  )
}
