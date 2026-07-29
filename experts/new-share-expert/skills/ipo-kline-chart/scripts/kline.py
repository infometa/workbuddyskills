#!/usr/bin/env python3
"""
A 股新股 K 线 / 分时绘制脚本（V2）
- 数据源：westock-data（腾讯自选股）
- 模式：day / week / month / minute
- 支持叠加：发行价水位线、上市日竖线、±30%/±60% 临停阈值
- 视觉：A 股红涨绿跌、底部数据源水印

用法：
    python3 kline.py sh688256 day --limit 60
    python3 kline.py sh688256 minute --issue-price 1198.00
    python3 kline.py sh688256 day --limit 30 --issue-price 1198 --listing-date 2026-04-15
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd

# ============ 配置 ============
DEFAULT_WESTOCK_PATHS = [
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/plugins/finance-data/skills/westock-data/scripts/index.js"
    ),
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/external_plugins/new-share-copilot/skills/westock-data/scripts/index.js"
    ),
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/experts/plugins/strategy-backtest-expert/skills/westock-data/scripts/index.js"
    ),
]

FONT_CANDIDATES = [
    # macOS
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    # Linux
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    # Windows
    "C:/Windows/Fonts/msyh.ttc",   # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf", # 黑体
    "C:/Windows/Fonts/simsun.ttc", # 宋体
]

UP_COLOR = "#E53935"
DOWN_COLOR = "#43A047"
MA_COLORS = {5: "#FB8C00", 20: "#1E88E5", 60: "#8E24AA"}

WATERMARK = "数据源：westock-data ｜ {ts} ｜ 仅供参考，不构成投资建议"


# ============ 工具 ============
def find_westock_script() -> str:
    # 1) 静态候选
    for p in DEFAULT_WESTOCK_PATHS:
        if os.path.isfile(p):
            return p
    # 2) 兜底：动态扫描 ~/.workbuddy 下所有 westock-data/scripts/index.js
    import glob
    for base in [
        os.path.expanduser("~/.workbuddy/plugins/marketplaces"),
        os.path.expanduser("~/.workbuddy/skills"),
    ]:
        if os.path.isdir(base):
            hits = glob.glob(
                os.path.join(base, "**/westock-data/scripts/index.js"),
                recursive=True,
            )
            if hits:
                return hits[0]
    raise FileNotFoundError(
        "未找到 westock-data 脚本。请确保已安装含 westock-data skill 的插件（如 finance-data、strategy-backtest-expert）。"
    )


def get_cjk_font():
    for path in FONT_CANDIDATES:
        if os.path.isfile(path):
            try:
                fm.fontManager.addfont(path)
            except Exception:
                pass
            return fm.FontProperties(fname=path)
    sys.stderr.write("⚠️ 中文字体未找到，将退化为英文标签\n")
    return None


def detect_board(code: str) -> str:
    code = code.lower()
    if code.startswith("sh688"):
        return "科创板"
    if code.startswith("sh60"):
        return "沪市主板"
    if code.startswith("sz30"):
        return "创业板"
    if code.startswith("sz000") or code.startswith("sz001") or code.startswith("sz002") or code.startswith("sz003"):
        return "深市主板"
    if code.startswith("bj"):
        return "北交所"
    return "未知板块"


def parse_table(stdout: str) -> list:
    rows = []
    for line in stdout.strip().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not cells:
            continue
        if all((c == "" or set(c) == {"-"}) for c in cells) and any(set(c) == {"-"} for c in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        return []
    header = rows[0]
    return [dict(zip(header, r)) for r in rows[1:]]


def run_westock(args: list) -> str:
    script = find_westock_script()
    cmd = ["node", script] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    if proc.returncode != 0:
        raise RuntimeError(f"westock-data 调用失败: {proc.stderr.strip()}")
    return proc.stdout


# ============ 数据获取 ============
def fetch_kline(code: str, period: str, limit: int) -> pd.DataFrame:
    out = run_westock(["kline", code, "--period", period, "--limit", str(limit), "--fq", "qfq"])
    rows = parse_table(out)
    if not rows:
        raise RuntimeError(f"K 线为空：code={code}, period={period}")
    data = []
    for r in rows:
        try:
            data.append({
                "Date": pd.Timestamp(r["date"]),
                "Open": float(r["open"]),
                "Close": float(r["last"]),
                "High": float(r["high"]),
                "Low": float(r["low"]),
                "Volume": float(r.get("volume", 0)),
            })
        except (KeyError, ValueError):
            continue
    if not data:
        raise RuntimeError("K 线解析失败")
    df = pd.DataFrame(data).sort_values("Date").set_index("Date")
    return df


def fetch_minute(code: str) -> pd.DataFrame:
    out = run_westock(["minute", code])
    rows = parse_table(out)
    if not rows:
        raise RuntimeError(f"分时为空：code={code}（可能是非交易日 / 早盘前 / 代码错误）")
    data = []
    for r in rows:
        try:
            t = r["time"]
            t = t.zfill(4)
            hh, mm = int(t[:2]), int(t[2:])
            data.append({
                "Time": f"{hh:02d}:{mm:02d}",
                "Price": float(r["price"]),
                "Volume": float(r.get("volume", 0)),
                "Amount": float(r.get("amount", 0)),
            })
        except (KeyError, ValueError):
            continue
    if not data:
        raise RuntimeError("分时解析失败")
    df = pd.DataFrame(data)
    df["AvgPrice"] = (df["Amount"].cumsum() / df["Volume"].replace(0, pd.NA).cumsum()).fillna(df["Price"])
    return df


# ============ 绘图：日/周/月 K ============
def draw_kline(df: pd.DataFrame, code: str, period: str, font, issue_price=None, listing_date=None, output_dir="."):
    fig = plt.figure(figsize=(14, 9), facecolor="white")
    ax_price = fig.add_axes([0.07, 0.30, 0.90, 0.60])
    ax_vol = fig.add_axes([0.07, 0.10, 0.90, 0.16])

    n = len(df)
    opens = df["Open"].values
    closes = df["Close"].values
    highs = df["High"].values
    lows = df["Low"].values
    vols = df["Volume"].values
    dates = df.index

    for i in range(n):
        color = UP_COLOR if closes[i] >= opens[i] else DOWN_COLOR
        body_bot = min(opens[i], closes[i])
        body_h = max(abs(closes[i] - opens[i]), 0.001 * max(abs(closes[i]), 1))
        ax_price.add_patch(plt.Rectangle((i - 0.3, body_bot), 0.6, body_h,
                                         facecolor=color, edgecolor=color, linewidth=0.8))
        ax_price.plot([i, i], [lows[i], highs[i]], color=color, linewidth=0.8)

    close_s = pd.Series(closes)
    for w, c in MA_COLORS.items():
        if n >= w:
            ma = close_s.rolling(window=w).mean()
            ax_price.plot(range(n), ma.values, color=c, linewidth=1.3, label=f"MA{w}")

    if issue_price:
        ax_price.axhline(y=float(issue_price), color="#FF6F00", linestyle="--", linewidth=1.5, alpha=0.85)
        label = f"发行价 {issue_price}" if font else f"Issue {issue_price}"
        ax_price.text(n - 1, float(issue_price), label, color="#FF6F00", fontsize=10,
                      fontproperties=font, va="bottom", ha="right",
                      bbox=dict(facecolor="white", edgecolor="#FF6F00", boxstyle="round,pad=0.2"))

    if listing_date:
        try:
            ld = pd.Timestamp(listing_date)
            idx_match = [i for i, d in enumerate(dates) if d.date() >= ld.date()]
            if idx_match:
                idx0 = idx_match[0]
                ax_price.axvline(x=idx0, color="#212121", linestyle="-", linewidth=1.2, alpha=0.7)
                label = f"上市日 {ld.strftime('%Y-%m-%d')}" if font else f"Listing {ld.strftime('%Y-%m-%d')}"
                ax_price.text(idx0, ax_price.get_ylim()[1], label, color="#212121",
                              fontsize=9, fontproperties=font, va="top", ha="left",
                              bbox=dict(facecolor="#FFF59D", edgecolor="#212121", boxstyle="round,pad=0.2"))
        except Exception as e:
            sys.stderr.write(f"⚠️ 上市日标注失败：{e}\n")

    ax_price.set_xlim(-1, n)
    ax_price.grid(True, linestyle="--", alpha=0.3)
    ax_price.legend(loc="upper left", fontsize=9)
    ax_price.set_ylabel("价格 (CNY)", fontproperties=font, fontsize=11)

    vol_colors = [UP_COLOR if closes[i] >= opens[i] else DOWN_COLOR for i in range(n)]
    ax_vol.bar(range(n), vols, color=vol_colors, width=0.6, alpha=0.85)
    ax_vol.set_xlim(-1, n)
    ax_vol.set_ylabel("成交量", fontproperties=font, fontsize=10)
    ax_vol.grid(True, linestyle="--", alpha=0.3)

    step = max(1, n // 10)
    ticks = list(range(0, n, step))
    labels = [dates[i].strftime("%Y-%m-%d") for i in ticks]
    ax_vol.set_xticks(ticks)
    ax_vol.set_xticklabels(labels, rotation=30, fontsize=8)
    ax_price.set_xticks(ticks)
    ax_price.set_xticklabels([])

    period_cn = {"day": "日 K", "week": "周 K", "month": "月 K"}.get(period, period)
    board = detect_board(code)
    title = f"{code}  {board} ｜ {period_cn} 线（共 {n} 根）"
    fig.suptitle(title, fontproperties=font, fontsize=15, y=0.97)

    last_close = closes[-1]
    chg = (closes[-1] - closes[-2]) / closes[-2] * 100 if n >= 2 else 0
    info = f"最新 {last_close:.2f} ｜ {dates[-1].strftime('%Y-%m-%d')} ｜ 涨跌 {chg:+.2f}%"
    ax_price.text(0.99, 0.97, info, transform=ax_price.transAxes, fontsize=10,
                  fontproperties=font, va="top", ha="right",
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFDE7", alpha=0.9))

    fig.text(0.5, 0.025, WATERMARK.format(ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
             ha="center", fontsize=8, color="#9E9E9E", fontproperties=font)

    os.makedirs(output_dir, exist_ok=True)
    fname = f"{code}_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join(output_dir, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ============ 绘图：分时 ============
def draw_minute(df: pd.DataFrame, code: str, font, issue_price=None, output_dir="."):
    fig = plt.figure(figsize=(14, 9), facecolor="white")
    ax_p = fig.add_axes([0.08, 0.30, 0.88, 0.60])
    ax_v = fig.add_axes([0.08, 0.10, 0.88, 0.16])

    n = len(df)
    x = list(range(n))
    prices = df["Price"].values
    avg = df["AvgPrice"].values
    vols = df["Volume"].diff().fillna(df["Volume"]).clip(lower=0).values

    ax_p.plot(x, prices, color="#E53935", linewidth=1.4, label="价格")
    ax_p.plot(x, avg, color="#1E88E5", linewidth=1.2, linestyle="--", label="均价")

    if issue_price:
        ip = float(issue_price)
        ax_p.axhline(y=ip, color="#FF6F00", linestyle="--", linewidth=1.4, alpha=0.85)
        ax_p.text(n - 1, ip, f"发行价 {ip}", fontproperties=font, color="#FF6F00",
                  fontsize=10, va="bottom", ha="right",
                  bbox=dict(facecolor="white", edgecolor="#FF6F00", boxstyle="round,pad=0.2"))
        # ±30% 临停阈值
        for pct, label, col in [(0.30, "+30%", "#9E9E9E"), (-0.30, "-30%", "#9E9E9E"),
                                (0.60, "+60%", "#616161"), (-0.60, "-60%", "#616161")]:
            y = prices[0] * (1 + pct) if n > 0 else ip * (1 + pct)
            ax_p.axhline(y=y, color=col, linestyle=":", linewidth=0.9, alpha=0.7)
            ax_p.text(0, y, f"{label} 临停线", fontproperties=font, color=col, fontsize=8, va="bottom", ha="left")

    ax_p.set_xlim(0, n)
    ax_p.grid(True, linestyle="--", alpha=0.3)
    ax_p.set_ylabel("价格 (CNY)", fontproperties=font, fontsize=11)
    ax_p.legend(loc="upper left", fontsize=9, prop=font)

    vol_colors = []
    last_p = None
    for p in prices:
        if last_p is None:
            vol_colors.append(UP_COLOR)
        else:
            vol_colors.append(UP_COLOR if p >= last_p else DOWN_COLOR)
        last_p = p
    ax_v.bar(x, vols, color=vol_colors, width=1.0, alpha=0.85)
    ax_v.set_xlim(0, n)
    ax_v.set_ylabel("分时成交量", fontproperties=font, fontsize=10)
    ax_v.grid(True, linestyle="--", alpha=0.3)

    step = max(1, n // 8)
    ticks = list(range(0, n, step))
    labels = [df.iloc[i]["Time"] for i in ticks]
    ax_v.set_xticks(ticks)
    ax_v.set_xticklabels(labels, rotation=0, fontsize=9)
    ax_p.set_xticks(ticks)
    ax_p.set_xticklabels([])

    board = detect_board(code)
    title = f"{code}  {board} ｜ 分时图（{df.iloc[0]['Time']}–{df.iloc[-1]['Time']}，共 {n} 分钟）"
    fig.suptitle(title, fontproperties=font, fontsize=15, y=0.97)

    last = prices[-1]
    chg_open = (prices[-1] - prices[0]) / prices[0] * 100 if prices[0] else 0
    info = f"最新 {last:.2f} ｜ 较开盘 {chg_open:+.2f}%"
    if issue_price:
        chg_ip = (last - float(issue_price)) / float(issue_price) * 100
        info += f" ｜ 较发行价 {chg_ip:+.2f}%"
    ax_p.text(0.99, 0.97, info, transform=ax_p.transAxes, fontsize=10,
              fontproperties=font, va="top", ha="right",
              bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFDE7", alpha=0.9))

    fig.text(0.5, 0.025, WATERMARK.format(ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
             ha="center", fontsize=8, color="#9E9E9E", fontproperties=font)

    os.makedirs(output_dir, exist_ok=True)
    fname = f"{code}_minute_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join(output_dir, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ============ 入口 ============
def main():
    ap = argparse.ArgumentParser(description="A 股新股 K 线/分时绘制 V2")
    ap.add_argument("code", help="股票代码 sh/sz/bj 前缀")
    ap.add_argument("mode", choices=["day", "week", "month", "minute"])
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--issue-price", type=float, default=None, help="发行价")
    ap.add_argument("--listing-date", type=str, default=None, help="上市日 YYYY-MM-DD")
    ap.add_argument("--output-dir", default=os.getcwd())
    args = ap.parse_args()

    if not re.match(r"^(sh|sz|bj)[0-9A-Za-z]+$", args.code):
        sys.stderr.write("❌ 代码格式错误，需以 sh/sz/bj 开头（本专家仅覆盖 A 股）\n")
        sys.exit(1)

    font = get_cjk_font()

    try:
        if args.mode == "minute":
            df = fetch_minute(args.code)
            path = draw_minute(df, args.code, font, args.issue_price, args.output_dir)
        else:
            df = fetch_kline(args.code, args.mode, args.limit)
            path = draw_kline(df, args.code, args.mode, font,
                              args.issue_price, args.listing_date, args.output_dir)
        print(f"CHART_PATH:{path}")
    except FileNotFoundError as e:
        sys.stderr.write(f"❌ {e}\n")
        sys.exit(3)
    except RuntimeError as e:
        sys.stderr.write(f"❌ {e}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
