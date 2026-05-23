import requests
import datetime
import os

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
        print(f"获取杠杆信息失败 (将显示 N/A): {e}")

    # 构建 Markdown 表头
    # 标的 | 方向 | 开仓价格 | 平仓价格 | 杠杆 | ROI
    md_content = "# Hyperliquid 交易记录\n\n"
    md_content += f"**最后更新 (UTC):** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md_content += "| 时间 (UTC) | 标的 | 方向 | 开仓价格 | 平仓价格 | 杠杆 | ROI |\n"
    md_content += "|---|---|---|---|---|---|---|\n"
    
    # 处理最近的 100 条记录
    for fill in fills[:100]:
        dt = datetime.datetime.fromtimestamp(fill['time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        coin = fill['coin']
        direction = fill['dir']
        px = float(fill['px'])
        sz = float(fill['sz'])
        pnl = float(fill.get('closedPnl', 0))
        
        leverage = leverage_map.get(coin, "N/A")
        
        open_px = "-"
        close_px = "-"
        roi_str = "-"
        
        if "Open" in direction:
            open_px = f"{px}"
        elif "Close" in direction:
            close_px = f"{px}"
            # 推算开仓价格: ExitPx - (Pnl/Size) * (1 if Long else -1)
            # 对于 Close Long, Pnl = (Exit - Entry) * Sz => Entry = Exit - Pnl/Sz
            # 对于 Close Short, Pnl = (Entry - Exit) * Sz => Entry = Exit + Pnl/Sz
            is_long = "Long" in direction
            try:
                if is_long:
                    calc_open_px = px - (pnl / sz)
                else:
                    calc_open_px = px + (pnl / sz)
                open_px = f"{calc_open_px:.4f}".rstrip('0').rstrip('.')
                
                # 计算 ROI (基于推算的开仓价格和杠杆)
                if leverage != "N/A" and calc_open_px > 0:
                    # ROI = Pnl / Margin = Pnl / (EntryPx * Sz / Leverage)
                    margin = (calc_open_px * sz) / float(leverage)
                    roi = (pnl / margin) * 100
                    roi_str = f"{roi:.2f}%"
            except:
                open_px = "Error"

        md_content += f"| {dt} | {coin} | {direction} | {open_px} | {close_px} | {leverage} | {roi_str} |\n"
        
    # 确保目录存在并写入文件
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"成功更新文件: {FILE_PATH}")
        
if __name__ == "__main__":
    fetch_and_update()
