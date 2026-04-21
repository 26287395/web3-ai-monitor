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
    """带重试机制的 AI 调用 (适配 2026 模型矩阵)"""
    # 强制指定 v1 稳定版路径
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

    # 2026 备选模型列表，按优先级尝试
    models_to_try = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
    
    max_retries = 5
    for attempt in range(max_retries):
        for model_name in models_to_try:
            try:
                print(f"正在尝试模型: {model_name} (第 {attempt + 1} 次尝试)...")
                response = client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                return response.text
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "429" in err_str:
                    print(f"⚠️ {model_name} 暂时拥堵，准备重试...")
                    continue
                else:
                    print(f"❌ 遇到非限制性错误: {e}")
                    raise e
        
        # 如果一轮模型都没通，等一会儿再试
        wait_time = (attempt + 1) * 10
        print(f"😴 全线拥堵，等待 {wait_time} 秒后重试...")
        time.sleep(wait_time)
        
    raise Exception("所有模型在多次重试后均不可用。")

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
        print("✅ Telegram 消息已送达！")
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
        print("未抓取到资讯")
        return

    try:
        analysis = ask_ai(all_news)
        send_tg(analysis)
    except Exception as e:
        print(f"💥 最终执行失败: {e}")

if __name__ == "__main__":
    main()
