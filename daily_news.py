import os
import requests
from datetime import datetime
from openai import OpenAI

# ====== 请替换以下配置（或使用环境变量） ======
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '你的DeepSeek API Key')
FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK', '你的飞书机器人Webhook地址')
# =============================================


def fetch_news():
    """1. 获取热点新闻（原始标题列表）"""
    try:
        resp = requests.get("https://60s.viki.moe/v2/60s", timeout=10)
        data = resp.json()
        news_list = data.get('data', [])
        # 将新闻列表拼接成带序号的字符串
        news_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(news_list)]) if news_list else "今日暂无新闻"
        return news_text
    except Exception as e:
        return f"获取新闻失败: {e}"


def ai_summarize(news_text):
    """2. 调用 DeepSeek API 生成申论素材总结"""
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    
    prompt = f"""
    请将以下热点新闻整理为申论备考素材，要求：
    1. 提炼核心论点
    2. 归纳可用的金句或对策
    3. 标注适用主题（如乡村振兴、社会治理、科技创新等）
    
    新闻：
    {news_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": "你是一位资深的申论辅导老师，擅长将时事热点转化为备考素材。"},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI总结失败: {e}"


def send_to_feishu(raw_news, summary):
    """3. 推送到飞书：先放原始新闻，再放AI总结（用户要求）"""
    today = datetime.now().strftime("%Y年%m月%d日")
    # 拼接消息：先标题+新闻，再分隔线，最后AI总结
    full_content = (
        f"📰 **{today} 申论备考早报**\n\n"
        f"【今日热点新闻】\n{raw_news}\n\n"
        f"---\n\n"
        f"【AI申论素材总结】\n{summary}"
    )
    
    message = {
        "msg_type": "text",
        "content": {"text": full_content}
    }
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=message, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"推送失败: {e}")
        return False


if __name__ == "__main__":
    print("开始获取新闻...")
    raw_news = fetch_news()
    print("新闻获取成功，正在进行AI加工...")
    summary = ai_summarize(raw_news)
    print("准备推送到飞书...")
    if send_to_feishu(raw_news, summary):   # 修改：同时传入原始新闻和总结
        print("✅ 推送成功！")
    else:
        print("❌ 推送失败，请检查Webhook地址。")