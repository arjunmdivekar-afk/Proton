"""High-Resolution Fully-Drawn Terminal Stock Price Chart in Indian Rupees (₹) and Global Currencies."""

import sys
from typing import List, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def render_stock_chart(
    prices: List[float],
    dates: Optional[List[str]] = None,
    symbol: str = "STOCK",
    timeframe: str = "1M",
    curr_symbol: str = "₹",
    width: int = 65,
    height: int = 11,
) -> str:
    """Render a fully drawn, continuous high-resolution stock price line chart using Braille sub-pixels."""
    if not prices or len(prices) < 2:
        return "[yellow]Insufficient price data to render chart.[/yellow]"

    # 2x4 sub-pixel resolution grid per character
    pixel_width = width * 2
    pixel_height = height * 4

    min_p = min(prices)
    max_p = max(prices)
    p_range = max_p - min_p if max_p != min_p else 1.0

    # Resample prices to pixel_width
    resampled_prices: List[float] = []
    resampled_dates: Optional[List[str]] = [] if dates else None
    n = len(prices)

    for x in range(pixel_width):
        idx = int((x / (pixel_width - 1)) * (n - 1))
        resampled_prices.append(prices[idx])
        if dates and resampled_dates is not None:
            resampled_dates.append(dates[min(idx, len(dates) - 1)])

    # Map prices to y-pixel coordinates (0 at bottom, pixel_height-1 at top)
    y_coords: List[int] = []
    for p in resampled_prices:
        norm = (p - min_p) / p_range
        y = int(round(norm * (pixel_height - 1)))
        y = max(0, min(pixel_height - 1, y))
        y_coords.append(y)

    # 2D sub-pixel canvas [y][x]
    canvas = [[0 for _ in range(pixel_width)] for _ in range(pixel_height)]

    # Draw continuous curve between adjacent horizontal points
    for x in range(pixel_width - 1):
        y1 = y_coords[x]
        y2 = y_coords[x + 1]
        step_y = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + step_y, step_y):
            canvas[y][x] = 1
    canvas[y_coords[-1]][pixel_width - 1] = 1

    # Convert 2D pixel canvas to Braille character grid [height][width]
    braille_grid = [[" " for _ in range(width)] for _ in range(height)]

    for char_y in range(height):
        base_py = (height - 1 - char_y) * 4
        for char_x in range(width):
            base_px = char_x * 2
            code = 0
            for dy in range(4):
                py = base_py + (3 - dy)
                if 0 <= py < pixel_height:
                    for dx in range(2):
                        px = base_px + dx
                        if px < pixel_width and canvas[py][px]:
                            if dx == 0:
                                if dy == 0: code |= 0x01
                                elif dy == 1: code |= 0x02
                                elif dy == 2: code |= 0x04
                                elif dy == 3: code |= 0x40
                            else:
                                if dy == 0: code |= 0x08
                                elif dy == 1: code |= 0x10
                                elif dy == 2: code |= 0x20
                                elif dy == 3: code |= 0x80

            if code != 0:
                braille_grid[char_y][char_x] = chr(0x2800 + code)

    # Trend calculation and styling
    first_p = prices[0]
    last_p = prices[-1]
    pct = ((last_p - first_p) / first_p) * 100 if first_p else 0.0
    color = "bold green" if pct >= 0 else "bold red"
    sign = "+" if pct >= 0 else ""

    lines = [
        f"[bold cyan]─── {symbol.upper()} Price Trend ({timeframe.upper()}) ───[/bold cyan] "
        f"[{color}]{sign}{pct:.2f}%[/{color}] [dim](Low: {curr_symbol}{min_p:,.2f} | High: {curr_symbol}{max_p:,.2f})[/dim]\n"
    ]

    # Format Y-axis prices with smooth curve rows
    for row_idx in range(height):
        price_at_row = max_p - (row_idx / (height - 1)) * p_range
        row_str = "".join(braille_grid[row_idx])
        lines.append(f"[dim]{curr_symbol}{price_at_row:>8.2f} │[/dim] [{color}]{row_str}[/{color}]")

    # X-axis divider
    lines.append("[dim]           └" + "─" * width + "[/dim]")

    # Timeline labels
    start_date = resampled_dates[0][:10] if resampled_dates else "Start"
    end_date = resampled_dates[-1][:10] if resampled_dates else "Latest"
    pad = width - len(start_date) - len(end_date)
    if pad > 0:
        lines.append(f"[dim]             {start_date}{' ' * pad}{end_date}[/dim]")

    return "\n".join(lines)


def render_sparkline(prices: List[float]) -> str:
    """Generate a compact, smooth 8-character sparkline."""
    if not prices or len(prices) < 2:
        return "---"
    chars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    min_p, max_p = min(prices), max(prices)
    diff = max_p - min_p if max_p != min_p else 1.0
    out = []
    step = max(1, len(prices) // 8)
    sampled = [prices[i] for i in range(0, len(prices), step)][:8]
    for p in sampled:
        idx = int(((p - min_p) / diff) * (len(chars) - 1))
        out.append(chars[max(0, min(len(chars) - 1, idx))])
    return "".join(out)
