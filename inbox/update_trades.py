import requests
import datetime
import os

# 你的 Hyperliquid 账户地址
ADDRESS = "0x6d4B0d128B994aa53fFCFF84A1D63eEa5a1294A8"
URL = "https://api.hyperliquid.xyz/info"
FILE_PATH = "docs/documents/proprietary-trading/jyjl.md"

def fetch_and_update():
    print(f"正在获取账户 {ADDRESS} 的交易记录...")
    # 构造请求参数获取交易历史
    payload = {"type": "userFills", "user": ADDRESS}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(URL, json=payload, headers=headers)
        response.raise_for_status()
        fills = response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return
    
    if not isinstance(fills, list):
        print(f"返回数据格式错误: {fills}")
        return

    # 构建 Markdown 格式表格
    md_content = "# Hyperliquid 交易记录\n\n"
    md_content += f"**最后更新 (UTC):** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md_content += "| 时间 (UTC) | 资产 | 方向 | 价格 | 数量 | 总价值 | 手续费 |\n"
    md_content += "|---|---|---|---|---|---|---|\n"
    
    # 提取最近的100条记录
    for fill in fills[:100]:
        # 时间戳转换为 readable 格式
        dt = datetime.datetime.fromtimestamp(fill['time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        coin = fill['coin']
        side = fill['dir']
        price = fill['px']
        sz = fill['sz']
        fee = fill.get('fee', '0')
        
        # 计算价值 (价格 * 数量)
        try:
            val = float(price) * float(sz)
            val_str = f"{val:.2f}"
        except:
            val_str = "N/A"
            
        md_content += f"| {dt} | {coin} | {side} | {price} | {sz} | {val_str} | {fee} |\n"
        
    # 确保目录存在并写入文件
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"成功更新文件: {FILE_PATH}")
        
if __name__ == "__main__":
    fetch_and_update()
