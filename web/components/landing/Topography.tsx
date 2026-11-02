const WIDTH = 1440;
const HEIGHT = 1200;
const HILLS: [number, number, number][] = [
  [0.16, 0.14, 1],
  [0.78, 0.3, 0.85],
  [0.46, 0.86, 0.95],
  [1.02, 0.9, 0.7],
];
const RINGS = 11;
const POINTS = 48;

function ringPath(cx: number, cy: number, radius: number, phase: number): string {
  const coords: [number, number][] = [];
  for (let index = 0; index < POINTS; index += 1) {
    const theta = (Math.PI * 2 * index) / POINTS;
    const wobble =
      1 +
      0.17 * Math.sin(3 * theta + phase) +
      0.08 * Math.sin(5 * theta + phase * 2.3) +
      0.04 * Math.sin(8 * theta + phase * 0.7);
    const x = cx + radius * wobble * Math.cos(theta) * 1.45;
    const y = cy + radius * wobble * Math.sin(theta) * 0.95;
    coords.push([x, y]);
  }

  const midpoint = (a: [number, number], b: [number, number]) =>
    [ (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 ] as [number, number];

  const first = midpoint(coords[POINTS - 1], coords[0]);
  let d = `M ${first[0].toFixed(1)} ${first[1].toFixed(1)}`;
  for (let index = 0; index < POINTS; index += 1) {
    const current = coords[index];
    const next = coords[(index + 1) % POINTS];
    const middle = midpoint(current, next);
    d += ` Q ${current[0].toFixed(1)} ${current[1].toFixed(1)} ${middle[0].toFixed(1)} ${middle[1].toFixed(1)}`;
  }
  return `${d} Z`;
}

function buildPaths(): string[] {
  const paths: string[] = [];
  HILLS.forEach(([hx, hy, scale], hillIndex) => {
    for (let ring = 1; ring <= RINGS; ring += 1) {
      const radius = ring * 26 * scale;
      paths.push(
        ringPath(
          hx * WIDTH,
          hy * HEIGHT,
          radius,
          ring * 0.28 + hillIndex * 1.7,
        ),
      );
    }
  });
  return paths;
}

const PATHS = buildPaths();

const LAYERS = [
  { key: "halo", width: 4, opacity: 0.035 },
  { key: "mid", width: 1.8, opacity: 0.06 },
  { key: "core", width: 1, opacity: 0.14 },
];

export function Topography() {
  return (
    <svg
      aria-hidden="true"
      className="h-full w-full"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="xMidYMid slice"
      fill="none"
      stroke="#ffffff"
    >
      <g className="topo-a">
        {LAYERS.map((layer) => (
          <g key={layer.key} strokeWidth={layer.width} strokeOpacity={layer.opacity}>
            {PATHS.filter((_, index) => index % 2 === 0).map((path, index) => (
              <path key={`a-${layer.key}-${index}`} d={path} />
            ))}
          </g>
        ))}
      </g>
      <g className="topo-b">
        {LAYERS.map((layer) => (
          <g key={layer.key} strokeWidth={layer.width} strokeOpacity={layer.opacity}>
            {PATHS.filter((_, index) => index % 2 === 1).map((path, index) => (
              <path key={`b-${layer.key}-${index}`} d={path} />
            ))}
          </g>
        ))}
      </g>
    </svg>
  );
}
