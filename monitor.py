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
    """适配 2026 年最新 API 架构，带智能重试逻辑"""
    # 强制锁定 v1 生产接口
    client = genai.Client(api_key=GEMINI_KEY, http_options={'api_version': 'v1'})
    
    prompt = f"请简要总结以下 Web3 资讯：\n{news_content}"

    # 2026 年 4 月目前最稳的模型列表
    # 3.1-flash-lite 是目前的 Free Tier 主力，429 概率最低
    models_to_try = [
        "gemini-3.1-flash-lite", 
        "gemini-1.5-flash-002", # 在 v1 路径下必须带后缀
        "gemini-3-flash"
    ]
    
    max_retries = 3
    for attempt in range(max_retries):
        for model_name in models_to_try:
            try:
                print(f"正在尝试模型: {model_name}...")
                response = client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                return response.text
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    print(f"⚠️ {model_name} 配额触发限制，正在切换或重试...")
                    continue
                elif "404" in err_msg:
                    print(f"⚠️ {model_name} 路径失效，跳过...")
                    continue
                else:
                    print(f"❌ 未知错误: {e}")
                    continue
        
        # 如果一轮全灭，等待后再试（指数退避）
        wait = (attempt + 1) * 30
        print(f"😴 暂时无可用模型，等待 {wait} 秒后进行下一轮尝试...")
        time.sleep(wait)
        
    raise Exception("所有 2026 预设模型均无法访问，请检查 Google AI Studio 账单状态。")

def send_tg(message):
    """发送逻辑：自动处理 Markdown 转义"""
    safe_text = message.replace("_", "\\_").replace("*", "\\*")
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": safe_text + "\n\n---\n来自 2026 监控助手", 
        "parse_mode": "Markdown"
    }
    
    res = requests.post(url, json=payload, timeout=15)
    if res.status_code == 200:
        print("✅ Telegram 推送成功！")
    else:
        # 降级发送纯文本
        payload.pop("parse_mode")
        requests.post(url, json=payload, timeout=15)
        print("✅ Telegram 降级推送成功！")

def main():
    sources = {"CD": "https://www.coindesk.com/arc/outboundfeeds/rss/"} # 示例源
    all_news = ""
    try:
        feed = feedparser.parse(sources["CD"])
        for entry in feed.entries[:5]: 
            all_news += f"- {entry.title}\n"
    except:
        pass
    
    if not all_news:
        print("未抓取到新闻")
        return

    try:
        analysis = ask_ai(all_news)
        send_tg(analysis)
    except Exception as e:
        print(f"💥 最终失败: {e}")

if __name__ == "__main__":
    main()
