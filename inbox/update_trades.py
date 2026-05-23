import requests
import datetime
import os
import re

# ================= 配置区 =================
ADDRESS = "0x6d4B0d128B994aa53fFCFF84A1D63eEa5a1294A8"
INFO_URL = "https://api.hyperliquid.xyz/info"
FILE_PATH = "docs/documents/proprietary-trading/jyjl.md"
# ==========================================

class HyperliquidTracker:
    def __init__(self, address):
        self.address = address
        self.session = requests.Session()

    def get_api_data(self):
        """获取成交记录和实时杠杆(仅限有仓位的)"""
        try:
            fills = self.session.post(INFO_URL, json={"type": "userFills", "user": self.address}).json()
            state = self.session.post(INFO_URL, json={"type": "clearinghouseState", "user": self.address}).json()
            lev_map = {p['position']['coin']: p['position']['leverage']['value'] 
                       for p in state.get('assetPositions', [])}
            return fills, lev_map
        except Exception as e:
            print(f"API请求失败: {e}")
            return [], {}

    def parse_history(self):
        """解析现有文件，提取历史记录和已知的杠杆记忆"""
        if not os.path.exists(FILE_PATH):
            return set(), [], {}
        
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        data_lines = [l.strip() for l in lines if l.startswith("| 20")]
        timestamps = set()
        history_lev_map = {}
        
        for l in data_lines:
            parts = [p.strip() for p in l.split("|")]
            if len(parts) >= 8:
                ts = parts[1]
                timestamps.add(ts)
                coin = parts[2]
                lev_str = parts[6].replace("x", "")
                if lev_str.isdigit():
                    history_lev_map[coin] = int(lev_str)
        
        return timestamps, data_lines, history_lev_map

    def process_fill(self, fill, lev_map, history_lev_map):
        """处理单笔成交，优先使用实时杠杆，其次使用历史记忆，最后默认为20x"""
        direction = fill['dir']
        if "Close" not in direction:
            return None

        dt = datetime.datetime.fromtimestamp(fill['time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        coin = fill['coin']
        px = float(fill['px'])
        sz = float(fill['sz'])
        pnl = float(fill.get('closedPnl', 0))
        
        # 杠杆优先级：1. API实时值 2. 文件历史值 3. 默认值20
        lev = lev_map.get(coin) or history_lev_map.get(coin) or 20
        
        is_long = "Long" in direction
        try:
            open_px = px - (pnl / sz) if is_long else px + (pnl / sz)
            if open_px <= 0: return None
            
            margin = (open_px * sz) / float(lev)
            roi = (pnl / margin) * 100
            return {
                "dt": dt, "coin": coin, "dir": direction,
                "open": f"{open_px:.4f}".rstrip('0').rstrip('.'),
                "close": f"{px}", "lev": f"{lev}x", "roi": roi
            }
        except:
            return None

    def update(self):
        # 1. 获取数据
        fills, api_lev_map = self.get_api_data()
        existing_ts, old_rows, history_lev_map = self.parse_history()
        
        # 2. 合并杠杆记忆
        combined_lev_map = {**history_lev_map, **api_lev_map}
        
        # 3. 处理新成交
        new_records = []
        for f in reversed(fills): # 从旧到新处理，确保杠杆记忆能更新
            data = self.process_fill(f, api_lev_map, history_lev_map)
            if data:
                # 更新历史记忆，供下一条记录使用
                history_lev_map[data['coin']] = int(data['lev'].replace("x", ""))
                if data['dt'] not in existing_ts:
                    row = f"| {data['dt']} | {data['coin']} | {data['dir']} | {data['open']} | {data['close']} | {data['lev']} | {data['roi']:.2f}% |"
                    new_records.append(row)
        
        # 将新纪录放在顶部
        all_rows = new_records[::-1] + old_rows
        if not all_rows:
            print("无可展示的数据")
            return

        # 4. 计算统计 (最近100笔)
        stats_data = all_rows[:100]
        wins, losses, p_sum, l_sum = 0, 0, 0.0, 0.0
        for r in stats_data:
            try:
                roi = float(r.split("|")[7].replace("%", "").strip())
                if roi > 0:
                    wins += 1; p_sum += roi
                elif roi < 0:
                    losses += 1; l_sum += abs(roi)
            except: continue
        
        total = wins + losses
        win_rate = f"{(wins/total*100):.2f}%" if total > 0 else "0%"
        pl_ratio = f"{(p_sum/wins)/(l_sum/losses):.2f}" if wins > 0 and losses > 0 else "N/A"

        # 5. 生成文件内容 (单行统计表)
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        content = [
            "# Hyperliquid 交易记录\n",
            f"> **更新时间:** {now_str} (UTC)  |  **胜率:** {win_rate}  |  **盈亏比:** {pl_ratio}\n",
            "### 历史成交明细",
            "| 时间 (UTC) | 标的 | 方向 | 开仓价格 | 平仓价格 | 杠杆 | ROI |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]
        content.extend(all_rows)

        # 6. 写入
        os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")
        
        print(f"更新成功: 新增 {len(new_records)} 笔, 胜率 {win_rate}, 盈亏比 {pl_ratio}")

if __name__ == "__main__":
    HyperliquidTracker(ADDRESS).update()
