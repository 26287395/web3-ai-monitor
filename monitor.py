import feedparser
import requests
import os
import time
from google import genai

# 从 GitHub Secrets 读取配置
# 请确保您已在 GitHub 仓库设置中配置了这三个变量
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_KEY")

def ask_ai(news_content):
    """
    调用 2026 年最新 Gemini 3.1 模型进行总结。
    针对截图中的【要闻】【机会】【情绪】格式进行了深度优化。
    """
    # 初始化客户端
    client = genai.Client(api_key=GEMINI_KEY)
    
    # 强制 AI 模仿您截图中的专业输出风格
    prompt = f"""
    你是一个 Web3 极简主义分析师。请根据以下资讯生成报告。
    
    资讯原文：
    {news_content}
    
    ---
    严格按照以下格式输出（禁止任何额外解释）：

    【要闻】
    1. [此处概括第一条新闻，末尾加来源缩写，如 (CD)]
    2. [第二条，来源缩写如 (TB)]
    3. [第三条，来源缩写如 (TB)]
    4. [第四条，来源缩写如 (DC)]
    5. [第五条，来源缩写如 (DC)]

    【机会】
    [提供 100 字左右的深度建议，涵盖技术实现逻辑、治理博弈或市场机会，风格需硬核专业。]

    【情绪】
    [两个字的中文词语，如“回暖”、“中性”或“震荡”]
    """

    # 按照您的截图，这是目前可用的模型优先级列表
    models_to_try = [
        "gemini-3.1-flash-lite-preview", 
        "gemini-3-flash-preview",
        "gemini-3.1-pro-preview"
    ]
    
    for model_name in models_to_try:
        try:
            print(f"正在尝试调用最新模型: {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            if response.text:
                return response.text
        except Exception as e:
            print(f"⚠️ 模型 {model_name} 暂时无法访问: {e}")
            continue
        
    raise Exception("所有 2026 预设模型均无法访问。请检查 API Key 权限或配额。")

def send_tg(message):
    """
    发送消息至 Telegram。
    包含自动转义逻辑，防止由于下划线等字符导致的解析错误。
    """
    # 底部链接
    footer = (
        "\n\n🔗 阅读原文：\n"
        "• CoinDesk: https://www.coindesk.com/\n"
        "• The Block: https://www.theblock.co/\n"
        "• Decrypt: https://decrypt.co/"
    )
    
    # 转义 MarkdownV2 容易报错的特殊字符（重点是下划线和星号）
    # 如果后续仍报错，建议将 parse_mode 设为 None
    safe_message = message.replace("_", "\\_").replace("*", "\\*")
    full_text = safe_message + footer
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": full_text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            print("✅ Telegram 消息推送成功！")
        else:
            print(f"⚠️ Markdown 发送失败，尝试纯文本兜底... 报错内容: {res.text}")
            payload.pop("parse_mode") # 移除 Markdown 解析
            payload["text"] = message + footer # 使用未处理的原始文本
            requests.post(url, json=payload, timeout=15)
            print("✅ Telegram 纯文本消息推送成功！")
    except Exception as e:
        print(f"❌ Telegram 发送过程中出现异常: {e}")

def main():
    # 定义 RSS 抓取源
    sources = {
        "CD": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "TB": "https://www.theblock.co/rss.xml",
        "DC": "https://decrypt.co/feed"
    }
    
    all_news = ""
    print("🚀 开始抓取全球 Web3 资讯...")
    for short_name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            # 每个源取前 5 条
            for entry in feed.entries[:5]: 
                all_news += f"[{short_name}] {entry.title}\n"
        except Exception as e:
            print(f"⚠️ 抓取 {short_name} 失败: {e}")
            continue
    
    if not all_news:
        print("⚠️ 未抓取到任何新闻，请检查 RSS 地址或网络。")
        return

    try:
        # 1. AI 总结
        analysis = ask_ai(all_news)
        # 2. 推送消息
        send_tg(analysis)
    except Exception as e:
        print(f"💥 运行崩溃: {e}")

if __name__ == "__main__":
    main()
