"""Terminal Stock Price Chart and Sparkline Renderer."""

from typing import List, Optional, Tuple


def render_stock_chart(
    prices: List[float],
    dates: Optional[List[str]] = None,
    symbol: str = "STOCK",
    timeframe: str = "1M",
    width: int = 55,
    height: int = 10,
) -> str:
    """Render a clean, ASCII terminal line chart with Y-axis price scale and timestamps."""
    if not prices or len(prices) < 2:
        return "[yellow]Insufficient price data to render chart.[/yellow]"

    n = len(prices)
    if n > width:
        step = n / width
        resampled_prices = [prices[int(i * step)] for i in range(width)]
        resampled_dates = [dates[int(i * step)] for i in range(width)] if dates and len(dates) == n else None
    else:
        resampled_prices = prices
        resampled_dates = dates

    min_val = min(resampled_prices)
    max_val = max(resampled_prices)
    val_range = max_val - min_val if max_val != min_val else 1.0

    num_cols = len(resampled_prices)
    grid = [[" " for _ in range(num_cols)] for _ in range(height)]

    # Calculate row index for each point
    row_indices = []
    for val in resampled_prices:
        norm = (val - min_val) / val_range
        r = int(round(norm * (height - 1)))
        r = max(0, min(height - 1, r))
        row_indices.append(r)

    # Plot points and connecting lines
    for col_idx in range(num_cols):
        r = height - 1 - row_indices[col_idx]
        grid[r][col_idx] = "*"

    for col_idx in range(num_cols - 1):
        r1 = height - 1 - row_indices[col_idx]
        r2 = height - 1 - row_indices[col_idx + 1]
        if r1 < r2:
            for r in range(r1 + 1, r2):
                grid[r][col_idx] = "\\"
        elif r1 > r2:
            for r in range(r2 + 1, r1):
                grid[r][col_idx] = "/"

    # Trend calculation
    first_p = resampled_prices[0]
    last_p = resampled_prices[-1]
    pct_change = ((last_p - first_p) / first_p) * 100 if first_p else 0.0
    trend_color = "green" if pct_change >= 0 else "red"
    trend_sign = "+" if pct_change >= 0 else ""

    lines = [
        f"[bold cyan]-- {symbol.upper()} Price Trend ({timeframe.upper()}) --[/bold cyan] "
        f"[{trend_color}]{trend_sign}{pct_change:.2f}%[/{trend_color}] "
        f"[dim](Low: ${min_val:.2f} | High: ${max_val:.2f})[/dim]\n"
    ]

    for row_idx in range(height):
        price_at_row = max_val - (row_idx / (height - 1)) * val_range
        row_str = "".join(grid[row_idx])
        lines.append(f"[dim]{price_at_row:>9.2f} |[/dim] [{trend_color}]{row_str}[/{trend_color}]")

    lines.append("[dim]          +-" + "-" * num_cols + "[/dim]")

    # X-axis timeline markers
    start_label = resampled_dates[0][:10] if resampled_dates else "Start"
    end_label = resampled_dates[-1][:10] if resampled_dates else "Latest"
    pad_len = num_cols - len(start_label) - len(end_label)
    if pad_len > 0:
        lines.append(f"[dim]            {start_label}{' ' * pad_len}{end_label}[/dim]")

    return "\n".join(lines)


def render_sparkline(prices: List[float]) -> str:
    """Generate a compact 8-character ASCII sparkline."""
    if not prices or len(prices) < 2:
        return "---"
    chars = ["_", ".", "-", "~", "=", "*", "^"]
    min_p, max_p = min(prices), max(prices)
    diff = max_p - min_p if max_p != min_p else 1.0
    out = []
    # Sample 8 points
    step = max(1, len(prices) // 8)
    sampled = [prices[i] for i in range(0, len(prices), step)][:8]
    for p in sampled:
        idx = int(((p - min_p) / diff) * (len(chars) - 1))
        out.append(chars[max(0, min(len(chars) - 1, idx))])
    return "".join(out)
