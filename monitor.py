import feedparser
import requests
import os
import time
from google import genai

# 配置信息
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """适配 2026 稳定版 API 的 AI 调用"""
    # 初始化客户端（不手动指定 api_version，让 SDK 自动协商最优路径）
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    你是一个 Web3 极简主义分析师。请将以下资讯压缩在 200 字以内的极简中文报告：
    {news_content}
    
    输出要求：
    1. 【要闻】列出 5 条最重磅动态，每条 30 字以内。
    2. 每条末尾标注来源：(CD) CoinDesk, (TB) The Block, (DC) Decrypt。
    3. 【机会】对开发者 @meng_dev 提供 1 条具体的开发或推文建议。
    4. 【情绪】一个中文词。
    """

    # 2026 年当前最稳模型列表
    # 如果你的 Key 权限较高，也可以把 'gemini-2.0-pro' 加入列表
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash-002"]
    
    for model_name in models_to_try:
        try:
            print(f"正在尝试调用模型: {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"⚠️ 模型 {model_name} 暂时无法访问: {e}")
            continue
        
    raise Exception("所有预设模型均 404 或不可用，请确认 Google AI Studio 中模型是否已更名。")

def send_tg(message):
    footer = (
        "\n\n🔗 **阅读原文：**\n"
        "• [CoinDesk](https://www.coindesk.com/)\n"
        "• [The Block](https://www.theblock.co/)\n"
        "• [Decrypt](https://decrypt.co/)"
    )
    full_text = message + footer
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": full_text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    res = requests.post(url, json=payload, timeout=10)
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
        print("⚠️ 未抓取到新闻数据。")
        return

    try:
        analysis = ask_ai(all_news)
        send_tg(analysis)
    except Exception as e:
        print(f"💥 最终执行失败: {e}")

if __name__ == "__main__":
    main()
