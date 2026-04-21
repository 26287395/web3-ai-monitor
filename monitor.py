import feedparser
import requests
import os
from google import genai # 使用全新的 SDK

# 配置参数
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """使用最新的 google-genai SDK 调用 Gemini"""
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    你是一个 Web3 极简主义分析师。请将以下资讯压缩在 250 字以内的中文报告：
    {news_content}
    
    输出要求：
    1. 【要闻】列出 5 条最重磅动态，每条 30 字以内。
    2. 每条要闻末尾标注来源简写：(CD) CoinDesk, (TB) The Block, (DC) Decrypt。
    3. 【机会】对开发者 @meng_dev 提供 1 条具体的开发或推文方向。
    4. 【情绪】一个中文词。
    
    注意：保持专业干练，禁止废话。
    """
    
    # 新 SDK 的调用方式
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents=prompt
    )
    return response.text

def send_tg(message):
    """发送消息到 Telegram"""
    footer = (
        "\n\n🔗 **阅读原文：**\n"
        "• [CoinDesk](https://www.coindesk.com/)\n"
        "• [The Block](https://www.theblock.co/)\n"
        "• [Decrypt](https://decrypt.co/)"
    )
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": message + footer, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

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
    
    if not all_news: return

    try:
        analysis = ask_ai(all_news)
        final_msg = f"🚀 **Web3 全球情报汇总**\n\n{analysis}"
        send_tg(final_msg)
        print("推送成功！")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
