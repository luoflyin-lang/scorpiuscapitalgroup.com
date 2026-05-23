import requests
import datetime
import os
import re

# 你的 Hyperliquid 账户地址
ADDRESS = "0x6d4B0d128B994aa53fFCFF84A1D63eEa5a1294A8"
INFO_URL = "https://api.hyperliquid.xyz/info"
FILE_PATH = "docs/documents/proprietary-trading/jyjl.md"

def fetch_and_update():
    print(f"正在获取账户 {ADDRESS} 的交易数据...")
    
    # 1. 获取交易记录 (Fills)
    try:
        fill_payload = {"type": "userFills", "user": ADDRESS}
        fill_resp = requests.post(INFO_URL, json=fill_payload)
        fill_resp.raise_for_status()
        fills = fill_resp.json()
    except Exception as e:
        print(f"获取交易记录失败: {e}")
        return

    # 2. 获取当前账户状态 (用于提取杠杆信息)
    leverage_map = {}
    try:
        state_payload = {"type": "clearinghouseState", "user": ADDRESS}
        state_resp = requests.post(INFO_URL, json=state_payload)
        state_resp.raise_for_status()
        asset_positions = state_resp.json().get('assetPositions', [])
        for pos in asset_positions:
            coin = pos['position']['coin']
            lev = pos['position']['leverage']['value']
            leverage_map[coin] = lev
    except Exception as e:
        print(f"获取杠杆信息失败: {e}")

    # 3. 读取现有文件
    existing_timestamps = set()
    file_exists = os.path.exists(FILE_PATH)
    if file_exists:
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                existing_timestamps = set(re.findall(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content))
        except:
            pass

    # 4. 筛选新记录
    new_rows = []
    for fill in fills:
        direction = fill['dir']
        if "Close" not in direction:
            continue
            
        dt = datetime.datetime.fromtimestamp(fill['time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        if dt in existing_timestamps:
            continue
            
        coin = fill['coin']
        px = float(fill['px'])
        sz = float(fill['sz'])
        pnl = float(fill.get('closedPnl', 0))
        leverage = leverage_map.get(coin, 10)
        
        is_long = "Long" in direction
        try:
            if is_long:
                calc_open_px = px - (pnl / sz)
            else:
                calc_open_px = px + (pnl / sz)
            open_px = f"{calc_open_px:.4f}".rstrip('0').rstrip('.')
            margin = (calc_open_px * sz) / float(leverage)
            roi = (pnl / margin) * 100
            roi_str = f"{roi:.2f}%"
            new_rows.append(f"| {dt} | {coin} | {direction} | {open_px} | {px} | {leverage}x | {roi_str} |")
        except:
            continue

    # 5. 获取所有数据行（新+旧）
    old_data_lines = []
    if file_exists:
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("| 20"):
                        old_data_lines.append(line.strip())
        except:
            pass

    all_data = new_rows + old_data_lines

    # 6. 计算统计数据 (最近 100 笔)
    stats_rows = all_data[:100]
    wins = 0
    losses = 0
    total_roi = 0.0
    profit_sum = 0.0
    loss_sum = 0.0
    
    for row in stats_rows:
        parts = row.split("|")
        if len(parts) < 8: continue
        try:
            roi_val = float(parts[7].replace("%", "").strip())
            total_roi += roi_val
            if roi_val > 0:
                wins += 1
                profit_sum += roi_val
            elif roi_val < 0:
                losses += 1
                loss_sum += abs(roi_val)
        except:
            continue
            
    total_count = wins + losses
    win_rate = f"{(wins / total_count * 100):.2f}%" if total_count > 0 else "0%"
    # 盈亏比 = 平均盈利 / 平均亏损
    avg_win = profit_sum / wins if wins > 0 else 0
    avg_loss = loss_sum / losses if losses > 0 else 0
    pl_ratio = f"{(avg_win / avg_loss):.2f}" if avg_loss > 0 else ("INF" if avg_win > 0 else "0.00")
    
    # 构建统计表格 (6列1行)
    summary_table = "## 交易表现统计 (最近100笔)\n\n"
    summary_table += "| 胜率 | 盈亏比 | 总ROI (累加) | 盈利笔数 | 亏损笔数 | 总计笔数 |\n"
    summary_table += "|---|---|---|---|---|---|\n"
    summary_table += f"| {win_rate} | {pl_ratio} | {total_roi:.2f}% | {wins} | {losses} | {total_count} |\n\n"

    # 7. 写入文件
    header = "# Hyperliquid 交易记录 (永久账本)\n\n"
    header += f"**最后更新时间 (UTC):** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    full_content = header + summary_table + "## 详细成交历史\n\n"
    full_content += "| 时间 (UTC) | 标的 | 方向 | 开仓价格 | 平仓价格 | 杠杆 | ROI |\n"
    full_content += "|---|---|---|---|---|---|---|\n"
    for row in all_data:
        full_content += row + "\n"
        
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(full_content)
    print(f"统计更新完成：胜率 {win_rate}, 总记录 {len(all_data)}")

if __name__ == "__main__":
    fetch_and_update()
