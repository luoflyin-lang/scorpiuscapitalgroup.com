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
        print(f"获取杠杆信息失败 (将显示 N/A): {e}")

    # 3. 读取现有文件，确定已有的最新记录时间
    existing_hashes = set()
    file_exists = os.path.exists(FILE_PATH)
    
    if file_exists:
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                # 使用正则表达式提取表格中的所有时间，作为简单的去重逻辑
                # 假设每行的时间格式是 202X-XX-XX XX:XX:XX
                existing_hashes = set(re.findall(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content))
        except Exception as e:
            print(f"读取旧文件失败，将重新创建: {e}")

    # 4. 筛选新记录
    new_rows = []
    # Fills API 返回的是按时间倒序排列的 (最新的在前)
    # 我们遍历一遍，只保留“平仓”且“不在已有记录中”的
    for fill in fills:
        direction = fill['dir']
        if "Close" not in direction:
            continue
            
        dt = datetime.datetime.fromtimestamp(fill['time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        # 如果时间戳已存在，说明是旧数据，停止处理（因为 API 是倒序的）
        if dt in existing_hashes:
            continue
            
        coin = fill['coin']
        px = float(fill['px'])
        sz = float(fill['sz'])
        pnl = float(fill.get('closedPnl', 0))
        leverage = leverage_map.get(coin, "N/A")
        
        close_px = f"{px}"
        roi_str = "-"
        
        is_long = "Long" in direction
        try:
            if is_long:
                calc_open_px = px - (pnl / sz)
            else:
                calc_open_px = px + (pnl / sz)
            open_px = f"{calc_open_px:.4f}".rstrip('0').rstrip('.')
            
            if leverage != "N/A" and calc_open_px > 0:
                margin = (calc_open_px * sz) / float(leverage)
                roi = (pnl / margin) * 100
                roi_str = f"{roi:.2f}%"
                
                # 保存为表格行
                new_rows.append(f"| {dt} | {coin} | {direction} | {open_px} | {close_px} | {leverage} | {roi_str} |")
        except:
            continue

    if not new_rows:
        print("没有发现新的成交记录。")
        return

    # 5. 写入或追加文件
    # 我们把最新的放在最上面，所以逻辑是：表头 + 新行 + 旧行
    
    header = "# Hyperliquid 交易记录 (永久账本)\n\n"
    header += f"**最后检查时间 (UTC):** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    header += "| 时间 (UTC) | 标的 | 方向 | 开仓价格 | 平仓价格 | 杠杆 | ROI |\n"
    header += "|---|---|---|---|---|---|---|\n"

    # 提取旧文件中的纯数据行
    old_data_lines = []
    if file_exists:
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("| 20"): # 只匹配日期开头的行
                        old_data_lines.append(line.strip())
        except:
            pass

    # 合并：新记录在旧记录之上
    all_data = new_rows + old_data_lines
    
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(header)
        for row in all_data:
            f.write(row + "\n")
            
    print(f"更新成功！新增 {len(new_rows)} 条记录，总计 {len(all_data)} 条记录。")
        
if __name__ == "__main__":
    fetch_and_update()
