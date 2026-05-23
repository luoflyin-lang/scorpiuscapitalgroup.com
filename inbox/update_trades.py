import requests
import datetime
import os
import re

# ================= 配置区 =================
ADDRESS = "0x6d4B0d128B994aa53fFCFF84A1D63eEa5a1294A8"
INFO_URL = "https://api.hyperliquid.xyz/info"
FILE_PATH = "docs/documents/proprietary-trading/jyjl.md"
DEFAULT_LEVERAGE = 10  # 当找不到实时杠杆时的默认值
# ==========================================

class HyperliquidTracker:
    def __init__(self, address):
        self.address = address
        self.session = requests.Session()

    def get_data(self):
        """一次性获取所有需要的数据"""
        try:
            # 获取成交记录
            fills = self.session.post(INFO_URL, json={"type": "userFills", "user": self.address}).json()
            # 获取账户状态(杠杆)
            state = self.session.post(INFO_URL, json={"type": "clearinghouseState", "user": self.address}).json()
            
            lev_map = {p['position']['coin']: p['position']['leverage']['value'] 
                       for p in state.get('assetPositions', [])}
            return fills, lev_map
        except Exception as e:
            print(f"数据抓取失败: {e}")
            return [], {}

    def parse_existing_data(self):
        """从现有文件中提取历史记录时间戳和数据行"""
        if not os.path.exists(FILE_PATH):
            return set(), []
        
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        data_lines = [l.strip() for l in lines if l.startswith("| 20")]
        timestamps = {re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", l).group() 
                      for l in data_lines if re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", l)}
        return timestamps, data_lines

    def calculate_roi_data(self, fill, lev_map):
        """计算单笔平仓记录的 ROI 信息"""
        direction = fill['dir']
        if "Close" not in direction:
            return None

        dt = datetime.datetime.fromtimestamp(fill['time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        coin = fill['coin']
        px = float(fill['px'])
        sz = float(fill['sz'])
        pnl = float(fill.get('closedPnl', 0))
        lev = lev_map.get(coin, DEFAULT_LEVERAGE)

        is_long = "Long" in direction
        try:
            # 反推开仓价
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
        fills, lev_map = self.get_data()
        existing_ts, old_rows = self.parse_existing_data()
        
        # 1. 处理新数据
        new_records = []
        for f in fills:
            data = self.calculate_roi_data(f, lev_map)
            if data and data['dt'] not in existing_ts:
                row = f"| {data['dt']} | {data['coin']} | {data['dir']} | {data['open']} | {data['close']} | {data['lev']} | {data['roi']:.2f}% |"
                new_records.append(row)
        
        all_rows = new_records + old_rows
        if not all_rows:
            print("无可展示的数据")
            return

        # 2. 计算统计信息 (仅限最近100笔)
        stats_data = all_rows[:100]
        wins, losses, p_sum, l_sum = 0, 0, 0.0, 0.0
        
        for r in stats_data:
            try:
                roi = float(r.split("|")[7].replace("%", "").strip())
                if roi > 0:
                    wins += 1
                    p_sum += roi
                elif roi < 0:
                    losses += 1
                    l_sum += abs(roi)
            except: continue
        
        total = wins + losses
        win_rate = f"{(wins/total*100):.2f}%" if total > 0 else "0%"
        pl_ratio = f"{(p_sum/wins)/(l_sum/losses):.2f}" if wins > 0 and losses > 0 else "N/A"

        # 3. 生成 Markdown
        content = [
            "# Hyperliquid 交易记录\n",
            f"**更新时间 (UTC):** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n",
            "### 账户表现统计 (最近100笔)\n",
            "| 胜率 | 盈亏比 |",
            "| :--- | :--- |",
            f"| {win_rate} | {pl_ratio} |\n",
            "### 历史成交明细\n",
            "| 时间 (UTC) | 标的 | 方向 | 开仓价格 | 平仓价格 | 杠杆 | ROI |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]
        content.extend(all_rows)

        # 4. 写入文件
        os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")
        
        print(f"更新完成: 新增 {len(new_records)} 笔, 胜率 {win_rate}, 盈亏比 {pl_ratio}")

if __name__ == "__main__":
    HyperliquidTracker(ADDRESS).update()
