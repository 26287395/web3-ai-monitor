import feedparser
import requests
import os
from google import genai

# 获取配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """使用 2026 年最新主流模型：Gemini 2.5 Flash"""
    # 强制指定 v1 稳定版路径，避免 SDK 默认去碰 v1beta
    client = genai.Client(api_key=GEMINI_KEY, http_options={'api_version': 'v1'})
    
    prompt = f"""
    你是一个 Web3 极简主义分析师。请将以下资讯压缩在 200 字以内的极简中文报告：
    {news_content}
    
    输出要求：
    1. 【要闻】列出 5 条最重磅动态，每条 30 字以内。
    2. 每条末尾标注来源：(CD) CoinDesk, (TB) The Block, (DC) Decrypt。
    3. 【机会】对开发者 @meng_dev 提供 1 条具体的开发或推文建议。
    4. 【情绪】一个中文词。
    """
    
    # 2026 年最稳型号是 gemini-2.5-flash，1.5 已经被部分地区下架
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    return response.text

def send_tg(message):
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
    
    if not all_news:
        print("未抓取到资讯")
        return

    try:
        # AI 分析并推送
        analysis = ask_ai(all_news)
        final_msg = f"🚀 **Web3 全球情报汇总**\n\n{analysis}"
        send_tg(final_msg)
        print("推送成功！使用的是 Gemini 2.5 Flash (v1 稳定版)")
    except Exception as e:
        print(f"执行失败: {e}")

if __name__ == "__main__":
    main()
