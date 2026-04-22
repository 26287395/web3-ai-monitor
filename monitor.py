import feedparser
import requests
import os
import time
from google import genai

# 获取配置 (请在 GitHub Secrets 更新你新生成的 Key)
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """适配 2026 年 4 月截图显示的最新模型"""
    # 初始化客户端
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"请简要总结以下 Web3 资讯：\n{news_content}"

    # 根据你提供的截图，这些是目前可用的最新模型
    models_to_try = [
        "gemini-3.1-flash-lite-preview", # 截图中的最轻量模型
        "gemini-3-flash-preview",        # 截图中的标准 Flash 模型
        "gemini-3.1-pro-preview"         # 截图中的高智能 Pro 模型
    ]
    
    for model_name in models_to_try:
        try:
            print(f"正在尝试调用最新模型: {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"⚠️ 模型 {model_name} 暂时无法访问: {e}")
            continue
        
    raise Exception("截图中的所有模型均无法访问，请检查新 Key 是否已在 GitHub Secrets 更新。")

def send_tg(message):
    """发送消息至 Telegram，带 Markdown 容错逻辑"""
    # 转义 Markdown 特殊字符，防止 TG 报 400 错误
    safe_text = message.replace("_", "\\_").replace("*", "\\*")
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": safe_text + "\n\n---\n来自 Gemini 3.1 监控助手", 
        "parse_mode": "Markdown"
    }
    
    res = requests.post(url, json=payload, timeout=15)
    if res.status_code != 200:
        # 如果 Markdown 失败，尝试纯文本发送
        payload.pop("parse_mode")
        requests.post(url, json=payload, timeout=15)

def main():
    # 抓取 CoinDesk RSS
    feed_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    all_news = ""
    try:
        print("正在抓取资讯...")
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]: 
            all_news += f"- {entry.title}\n"
    except:
        pass
    
    if not all_news:
        print("未抓取到新闻，请检查网络或 RSS 链接。")
        return

    try:
        analysis = ask_ai(all_news)
        send_tg(analysis)
        print("✅ 任务完成，消息已推送到 Telegram！")
    except Exception as e:
        print(f"💥 最终执行失败: {e}")

if __name__ == "__main__":
    main()
