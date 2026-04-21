import feedparser
import requests
import os
import time
from google import genai

# 从 GitHub Secrets 获取配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """适配 2026 稳定版 API 的 AI 调用，带重试机制"""
    # 初始化客户端，SDK 会自动协商最优路径
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    你是一个 Web3 极简主义分析师。请将以下资讯压缩在 200 字以内的极简中文报告：
    {news_content}
    
    输出要求：
    1. 【要闻】列出 5 条最重磅动态，每条 30 字以内。
    2. 每条末尾标注来源：(CD) CoinDesk, (TB) The Block, (DC) Decrypt。
    3. 【机会】对开发者 @meng_dev 提供 1 条具体的开发或推文建议。
    4. 【情绪】一个中文词。
    
    注意：严格禁止废话，禁止输出除术语外的英文。
    """

    # 2026 年当前最稳模型列表
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]
    
    for model_name in models_to_try:
        try:
            print(f"正在尝试调用 AI 模型: {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"⚠️ 模型 {model_name} 暂时无法访问: {e}")
            continue
        
    raise Exception("所有预设 AI 模型均不可用，请检查 API Key 权限或配额。")

def send_tg(message):
    """发送消息至 Telegram，带 Markdown 自动转义和容错逻辑"""
    footer = (
        "\n\n🔗 **阅读原文：**\n"
        "• [CoinDesk](https://www.coindesk.com/)\n"
        "• [The Block](https://www.theblock.co/)\n"
        "• [Decrypt](https://decrypt.co/)"
    )
    
    # 打印生成的原文，方便在 GitHub Actions 日志中查看
    print("\n--- [AI 生成内容展示] ---")
    print(message)
    print("------------------------\n")

    # 1. 预处理：转义 Markdown 特殊字符，防止 TG 报 400 错误
    # 注意：下划线 _ 是最容易导致 Bad Request 的元凶
    safe_message = message.replace("_", "\\_").replace("*", "\\*")
    full_text = safe_message + footer
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    
    # 2. 尝试使用 Markdown 模式发送
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": full_text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    res = requests.post(url, json=payload, timeout=15)
    
    # 3. 容错逻辑：如果 Markdown 解析失败（Code 400），降级为纯文本发送
    if res.status_code != 200:
        print(f"⚠️ Markdown 发送失败 (可能是字符冲突)，正在尝试纯文本模式重发...")
        payload.pop("parse_mode")
        payload["text"] = message + "\n\n(注：Markdown 解析失败，已转为纯文本推送)" + footer
        res = requests.post(url, json=payload, timeout=15)
        
    if res.status_code == 200:
        print("✅ Telegram 消息推送成功！")
    else:
        print(f"❌ TG 发送最终失败: {res.text}")

def main():
    # 定义新闻源
    sources = {
        "CD": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "TB": "https://www.theblock.co/rss.xml",
        "DC": "https://decrypt.co/feed"
    }
    
    all_news = ""
    print("正在抓取全球 Web3 资讯...")
    for short_name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: 
                all_news += f"[{short_name}] {entry.title}\n"
        except Exception as e:
            print(f"⚠️ 无法抓取 {short_name}: {e}")
            continue
    
    if not all_news:
        print("⚠️ 未抓取到有效新闻数据，脚本退出。")
        return

    try:
        # 步骤 1: AI 总结
        analysis = ask_ai(all_news)
        # 步骤 2: 推送 Telegram
        send_tg(analysis)
    except Exception as e:
        print(f"💥 运行崩溃: {e}")

if __name__ == "__main__":
    main()
