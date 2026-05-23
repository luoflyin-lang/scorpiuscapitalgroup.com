import requests
import datetime
import os
import re

# ================= 配置区 =================
ADDRESS = "0x6d4B0d128B994aa53fFCFF84A1D63eEa5a1294A8"
INFO_URL = "https://api.hyperliquid.xyz/info"
FILE_PATH = "docs/documents/proprietary-trading/jyjl.md"
FIXED_MULTIPLIER = 10  # 用户要求的 10 倍固定乘数
# ==========================================

class HyperliquidTracker:
    def __init__(self, address):
        self.address = address
        self.session = requests.Session()

    def get_api_data(self):
        """获取成交记录"""
        try:
            return self.session.post(INFO_URL, json={"type": "userFills", "user": self.address}).json()
        except Exception as e:
            print(f"API请求失败: {e}")
            return []

    def parse_history(self):
        """解析现有文件，提取历史记录时间戳"""
        if not os.path.exists(FILE_PATH):
            return set(), []
        
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        data_lines = [l.strip() for l in lines if l.startswith("| 20")]
        timestamps = {re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", l).group() 
                      for l in data_lines if re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", l)}
        return timestamps, data_lines

    def process_fill(self, fill):
        """处理单笔成交，使用固定 10 倍乘数计算 ROI"""
        direction = fill['dir']
        if "Close" not in direction:
            return None

        dt = datetime.datetime.fromtimestamp(fill['time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        coin = fill['coin']
        px = float(fill['px'])
        sz = float(fill['sz'])
        pnl = float(fill.get('closedPnl', 0))
        
        is_long = "Long" in direction
        try:
            # 反推开仓价 (此价格用于展示)
            open_px_val = px - (pnl / sz) if is_long else px + (pnl / sz)
            if open_px_val <= 0: return None
            
            # 计算价格变动百分比
            # Price Change % = (Pnl / (EntryPx * Sz))
            price_change_pct = pnl / (open_px_val * sz)
            # 用户要求的 ROI = 价格变动 % * 10
            roi = price_change_pct * 100 * FIXED_MULTIPLIER
            
            return {
                "dt": dt, "coin": coin, "dir": direction,
                "open": f"{open_px_val:.4f}".rstrip('0').rstrip('.'),
                "close": f"{px}", "roi": roi
            }
        except:
            return None

    def update(self):
        # 1. 获取数据
        fills = self.get_api_data()
        existing_ts, old_rows = self.parse_history()
        
        # 2. 处理新成交
        new_records = []
        for f in fills:
            data = self.process_fill(f)
            if data and data['dt'] not in existing_ts:
                row = f"| {data['dt']} | {data['coin']} | {data['dir']} | {data['open']} | {data['close']} | {data['roi']:.2f}% |"
                new_records.append(row)
        
        # 新记录在顶部
        all_rows = new_records + old_rows
        if not all_rows:
            print("无可展示的数据")
            return

        # 3. 计算统计 (最近100笔)
        stats_data = all_rows[:100]
        wins, losses, p_sum, l_sum = 0, 0, 0.0, 0.0
        for r in stats_data:
            try:
                roi = float(r.split("|")[6].replace("%", "").strip())
                if roi > 0:
                    wins += 1; p_sum += roi
                elif roi < 0:
                    losses += 1; l_sum += abs(roi)
            except: continue
        
        total = wins + losses
        win_rate = f"{(wins/total*100):.2f}%" if total > 0 else "0%"
        pl_ratio = f"{(p_sum/wins)/(l_sum/losses):.2f}" if wins > 0 and losses > 0 else "N/A"

        # 4. 生成内容
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        content = [
            "# Hyperliquid 交易记录\n",
            f"> **更新时间:** {now_str} (UTC)  |  **胜率:** {win_rate}  |  **盈亏比:** {pl_ratio}\n",
            "### 历史成交明细",
            "| 时间 (UTC) | 标的 | 方向 | 开仓价格 | 平仓价格 | ROI (10x) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]
        content.extend(all_rows)

        # 5. 写入
        os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")
        
        print(f"更新成功: 胜率 {win_rate}, 盈亏比 {pl_ratio}")

if __name__ == "__main__":
    HyperliquidTracker(ADDRESS).update()
