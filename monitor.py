import feedparser
import requests
import os
from google import genai # 必须使用新版 SDK 导入

# 配置参数
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """使用 2026 年最新的 Gemini 2.0 Flash 模型"""
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    你是一个 Web3 极简主义分析师。请将以下资讯压缩在 200 字以内的极简中文报告：
    {news_content}
    
    输出要求：
    1. 【要闻】列出 5 条最重磅动态，每条 30 字以内。
    2. 每条要闻末尾标注来源：(CD) CoinDesk, (TB) The Block, (DC) Decrypt。
    3. 【机会】对开发者 @meng_dev 提供 1 条具体的开发或推文建议。
    4. 【情绪】一个中文词。
    
    注意：禁止输出任何英文（术语除外），严禁废话。
    """
    
    # 调用 Gemini 2.0 Flash
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    return response.text

def send_tg(message):
    """发送中文消息到 Telegram"""
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
        except Exception as e:
            print(f"抓取 {short_name} 失败: {e}")
            continue
    
    if not all_news:
        print("未抓取到资讯")
        return

    try:
        analysis = ask_ai(all_news)
        final_msg = f"🚀 **Web3 全球情报汇总**\n\n{analysis}"
        send_tg(final_msg)
        print("推送成功！正在使用 Gemini 2.0 Flash")
    except Exception as e:
        print(f"AI 分析或发送失败: {e}")

if __name__ == "__main__":
    main()
