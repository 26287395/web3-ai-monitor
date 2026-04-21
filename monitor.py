import feedparser
import requests
import os
from google import genai

# 从 GitHub Secrets 获取配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """使用 2026 年主流模型 Gemini 2.5 Flash"""
    # 强制指定 v1 稳定版路径，解决 404 问题
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
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    return response.text

def send_tg(message):
    """发送消息并打印详细结果"""
    footer = (
        "\n\n🔗 **阅读原文：**\n"
        "• [CoinDesk](https://www.coindesk.com/)\n"
        "• [The Block](https://www.theblock.co/)\n"
        "• [Decrypt](https://decrypt.co/)"
    )
    full_text = message + footer
    
    # 打印即将发送的内容（用于调试）
    print("\n--- [准备发送至 Telegram 的内容] ---")
    print(full_text)
    print("-----------------------------------\n")
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": full_text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        # 打印 Telegram 服务器的反馈
        if response.status_code == 200:
            print(f"✅ Telegram 发送成功！响应详情: {response.text}")
        else:
            print(f"❌ Telegram 发送失败！错误码: {response.status_code}")
            print(f"❌ 失败原因: {response.text}")
            print(f"💡 提示：请检查 TG_TOKEN 是否正确，以及你是否给 Bot 发过 /start")
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")

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
        print("⚠️ 未抓取到任何新闻，请检查 RSS 源是否可用。")
        return

    try:
        # AI 生成内容
        analysis = ask_ai(all_news)
        # 执行发送操作
        send_tg(analysis)
    except Exception as e:
        print(f"💥 脚本运行崩溃: {e}")

if __name__ == "__main__":
    main()
