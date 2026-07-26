import os
import requests
from datetime import datetime
from openai import OpenAI

# ====== 请替换以下配置（或使用环境变量） ======
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'null')
FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK', 'null')
# =============================================



def fetch_news():
    """1. 获取热点新闻（从 data.news 中提取）"""
    try:
        resp = requests.get("https://60s.viki.moe/v2/60s", timeout=10)
        data = resp.json()
        news_list = data.get('data', {}).get('news', [])
        news_list = news_list[:15]
        if news_list:
            news_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(news_list)])
        else:
            news_text = "今日暂无新闻"
        return news_text
    except Exception as e:
        return f"获取新闻失败: {e}"


def ai_summarize(news_text):
    """2. 调用 DeepSeek API 生成申论素材总结（结构化纯文本）"""
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    
    prompt = f"""
    请将以下热点新闻整理为申论备考素材，要求结构清晰，层次分明。
    
    【输出格式要求】（严格遵守）
    一、核心论点（用“一、”作为大标题）
      1. 论点一（用“1.”作为小标题）
      2. 论点二
      3. 论点三
    
    二、金句积累（用“二、”作为大标题）
      1. 金句一
      2. 金句二
    
    三、对策建议（用“三、”作为大标题）
      1. 对策一
      2. 对策二
    
    四、适用主题（用“四、”作为大标题，用逗号分隔关键词）
      主题一，主题二，主题三
    
    【重要】使用中文序号（一、二、三）和数字序号（1. 2. 3.），
    配合换行和缩进来区分层级。适当使用emoji来增强可读性。不要使用任何 Markdown 标记。
    
    新闻：
    {news_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": "你是一位资深的申论辅导老师，擅长将时事热点转化为备考素材。输出时必须严格按照用户指定的格式：大标题用“一、二、三”，子标题用“1. 2. 3.”，适当使用emoji来增强可读性，不用Markdown。"},
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
    """3. 推送到飞书：纯文本格式，使用序号和emoji排版"""
    today = datetime.now().strftime("%Y年%m月%d日")
    full_content = (
        f"☝🏻️🤓早上好 义人，这是 {today} 的早报😘\n\n"
        f"【今日热点新闻】\n{raw_news}\n\n"
        f"----------\n\n"
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
    if send_to_feishu(raw_news, summary):
        print("✅ 推送成功！")
    else:
        print("❌ 推送失败，请检查Webhook地址。")