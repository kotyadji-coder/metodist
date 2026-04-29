"""Generate a real maze using recursive backtracking.

Returns SVG string for embedding in HTML template.
"""

import random


def generate_maze(rows: int = 12, cols: int = 16, seed: int | None = None) -> dict:
    """Generate a maze grid and return SVG representation.

    Returns:
        {
            "svg": str (SVG markup),
            "rows": int,
            "cols": int,
        }
    """
    if seed is not None:
        random.seed(seed)

    # Each cell has walls: top, right, bottom, left
    # True = wall exists
    grid = [[{"top": True, "right": True, "bottom": True, "left": True} for _ in range(cols)] for _ in range(rows)]
    visited = [[False] * cols for _ in range(rows)]

    def neighbors(r, c):
        dirs = []
        if r > 0:
            dirs.append((r - 1, c, "top", "bottom"))
        if r < rows - 1:
            dirs.append((r + 1, c, "bottom", "top"))
        if c > 0:
            dirs.append((r, c - 1, "left", "right"))
        if c < cols - 1:
            dirs.append((r, c + 1, "right", "left"))
        return dirs

    # Recursive backtracking with explicit stack
    stack = [(0, 0)]
    visited[0][0] = True

    while stack:
        r, c = stack[-1]
        unvisited = [(nr, nc, wall, opp) for nr, nc, wall, opp in neighbors(r, c) if not visited[nr][nc]]
        if unvisited:
            nr, nc, wall, opp = random.choice(unvisited)
            grid[r][c][wall] = False
            grid[nr][nc][opp] = False
            visited[nr][nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()

    # Build SVG
    cell_size = 28
    wall_w = 2
    w = cols * cell_size
    h = rows * cell_size
    pad = 4

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + pad * 2} {h + pad * 2}" '
                 f'width="{w + pad * 2}" height="{h + pad * 2}">')

    # Background
    lines.append(f'<rect x="0" y="0" width="{w + pad * 2}" height="{h + pad * 2}" fill="white"/>')

    # Draw walls
    lines.append(f'<g stroke="#1f2937" stroke-width="{wall_w}" stroke-linecap="round">')

    for r in range(rows):
        for c in range(cols):
            x = pad + c * cell_size
            y = pad + r * cell_size

            if grid[r][c]["top"]:
                # Don't draw top wall for entrance (top-left)
                if not (r == 0 and c == 0):
                    lines.append(f'<line x1="{x}" y1="{y}" x2="{x + cell_size}" y2="{y}"/>')

            if grid[r][c]["left"]:
                if not (r == 0 and c == 0):
                    lines.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + cell_size}"/>')

            if grid[r][c]["right"]:
                # Don't draw right wall for exit (bottom-right)
                if not (r == rows - 1 and c == cols - 1):
                    lines.append(f'<line x1="{x + cell_size}" y1="{y}" x2="{x + cell_size}" y2="{y + cell_size}"/>')

            if grid[r][c]["bottom"]:
                if not (r == rows - 1 and c == cols - 1):
                    lines.append(f'<line x1="{x}" y1="{y + cell_size}" x2="{x + cell_size}" y2="{y + cell_size}"/>')

    lines.append('</g>')

    # Start arrow
    sx = pad - 2
    sy = pad + cell_size // 2
    lines.append(f'<text x="{sx}" y="{sy}" font-size="14" font-weight="900" fill="#16a34a" '
                 f'text-anchor="end" dominant-baseline="middle" font-family="Nunito, sans-serif">СТАРТ</text>')

    # Finish arrow
    ex = pad + w + 2
    ey = pad + h - cell_size // 2
    lines.append(f'<text x="{ex}" y="{ey}" font-size="14" font-weight="900" fill="#dc2626" '
                 f'text-anchor="start" dominant-baseline="middle" font-family="Nunito, sans-serif">ФИНИШ</text>')

    lines.append('</svg>')

    return {
        "svg": "\n".join(lines),
        "rows": rows,
        "cols": cols,
    }
