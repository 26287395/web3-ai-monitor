# 🚀 Web3 全球情报监控站 (AI Powered)

本项目是一个专为 **@meng_dev** 打造的自动化 Web3 资讯聚合与分析工具。它利用 GitHub Actions 周期性抓取全球顶级加密媒体，并通过 Google Gemini AI 进行极致浓缩，最后推送到 Telegram。

## 🌟 核心功能

* **多源聚合**：整合 CoinDesk, The Block 和 Decrypt 三大权威信源。
* **AI 深度浓缩**：利用 Gemini 1.5 Flash 将海量资讯压缩至 200 字以内的中文。

## 🛠️ 技术栈

* **Python**: 核心抓取与逻辑处理。
* **Gemini 1.5 Flash**: AI 总结与机会分析。
* **GitHub Actions**: 自动化任务调度（每 4 小时运行一次）。
* **Telegram Bot**: 结果即时推送。

## ⚙️ 环境配置 (Secrets)

运行此项目需要在 GitHub Settings -> Secrets 中配置以下变量：

| 变量名 | 描述 | 获取渠道 |
| :--- | :--- | :--- |
| `TG_TOKEN` | Telegram Bot API Token | @BotFather |
| `TG_CHAT_ID` | 你的 Telegram 用户 ID | @userinfobot |
| `GEMINI_KEY` | Google AI Studio API Key | [Google AI Studio](https://aistudio.google.com/) |

## 📂 目录结构

```text
.
├── .github/workflows/
│   └── monitor.yml      # GitHub Actions 定时任务配置
├── monitor.py           # 核心爬虫与 AI 逻辑脚本
└── README.md            # 项目说明文档
