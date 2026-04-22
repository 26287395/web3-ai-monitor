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
    """适配 2026 年 4 月配额最稳的模型"""
    # 强制走 v1 稳定路径，不再尝试 v1beta
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

    # 2026 年当前 Free Tier 建议模型列表
    # gemini-3.1-flash-lite 是目前最不容易报 429 的模型
    models_to_try = [
        "gemini-3.1-flash-lite", 
        "gemini-3.0-flash",
        "gemini-1.5-flash-002"
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
            print(f"⚠️ 模型 {model_name} 报错: {e}")
            continue
        
    raise Exception("所有 2026 预设模型均无法访问。请确认 Google AI Studio 是否有新的模型更名公告。")

def send_tg(message):
    footer = (
        "\n\n🔗 **阅读原文：**\n"
        "• [CoinDesk](https://www.coindesk.com/)\n"
        "• [The Block](https://www.theblock.co/)\n"
        "• [Decrypt](https://decrypt.co/)"
    )
    
    # 转义 Markdown 敏感字符防止 400 错误
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
    if res.status_code != 200:
        print(f"⚠️ Markdown 失败，尝试纯文本发送...")
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
        print("⚠️ 未抓取到新闻数据。")
        return

    try:
        analysis = ask_ai(all_news)
        send_tg(analysis)
    except Exception as e:
        print(f"💥 最终执行失败: {e}")

if __name__ == "__main__":
    main()
