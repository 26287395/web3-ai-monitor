import feedparser
import requests
import os
import time
from google import genai

# 获取配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """适配 2026 年 4 月配额最稳的模型矩阵"""
    # 强制锁定 v1 稳定版路径，避免被重定向至已失效的测试接口
    client = genai.Client(api_key=GEMINI_KEY, http_options={'api_version': 'v1'})
    
    prompt = f"""
    你是一个 Web3 极简主义分析师。请将以下资讯压缩在 200 字以内的极简中文报告：
    {news_content}
    
    输出要求：
    1. 【要闻】列出 5 条最重磅动态，每条 30 字以内。
    2. 每条末尾标注来源：(CD) CoinDesk, (TB) The Block, (DC) Decrypt。
    3. 【机会】对开发者 @meng_dev 提供 1 条具体的推文建议。
    4. 【情绪】一个中文词。
    """

    # 2026 年当前 Free Tier 建议模型优先级
    # gemini-3.1-flash-lite 是目前官方主推的低功耗、高配额模型
    models_to_try = [
        "gemini-3.1-flash-lite", 
        "gemini-1.5-flash-002", # 必须带后缀 002 才能在 v1 路径识别
        "gemini-2.0-flash-exp"
    ]
    
    for model_name in models_to_try:
        try:
            print(f"正在尝试 2026 核心模型: {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            return response.text
        except Exception as e:
            # 捕获 429 并打印，方便观察是否触发频率限制
            print(f"⚠️ 模型 {model_name} 暂时不可用 (报错: {e})")
            continue
        
    raise Exception("所有 2026 预设模型均无法访问。请检查 API Key 是否有效。")

def send_tg(message):
    footer = (
        "\n\n🔗 **阅读原文：**\n"
        "• [CoinDesk](https://www.coindesk.com/)\n"
        "• [The Block](https://www.theblock.co/)\n"
        "• [Decrypt](https://decrypt.co/)"
    )
    
    # 核心修复：转义 Markdown 特殊字符，防止 Telegram 报 400 错误
    safe_message = message.replace("_", "\\_").replace("*", "\\*")
    full_text = safe_message + footer
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": full_text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    res = requests.post(url, json=payload, timeout=15)
    
    # 如果 Markdown 解析失败，自动切换为纯文本重发
    if res.status_code != 200:
        print(f"⚠️ Markdown 发送失败，尝试纯文本模式...")
        payload.pop("parse_mode")
        res = requests.post(url, json=payload, timeout=15)
        
    if res.status_code == 200:
        print("✅ Telegram 消息发送成功！")
    else:
        print(f"❌ TG 发送失败: {res.text}")

def main():
    sources = {
        "CD": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "TB": "https://www.theblock.co/rss.xml",
        "DC": "https://decrypt.co/feed"
    }
    
    all_news = ""
    for short_name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: 
                all_news += f"[{short_name}] {entry.title}\n"
        except:
            continue
    
    if not all_news:
        print("⚠️ 未抓取到新闻，RSS 源可能被反爬。")
        return

    try:
        analysis = ask_ai(all_news)
        send_tg(analysis)
    except Exception as e:
        print(f"💥 运行崩溃: {e}")

if __name__ == "__main__":
    main()
