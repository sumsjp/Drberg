from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('youtube_update')

prompts = [
'''您是個專業的文件整理員
''',
           
'''# 工作目標：
1. 用 中文 整理文稿
# 輸出要求:
1. 只能用 中文 回答
'''
]

templates = [
'''
請用 中文 整理下面文稿:\n
{text}
''',

'''
===== 文章開始 =====
{text}
===== 文章結束 =====\n
請用 中文 整理上面文稿:
''',
]

models = {
    "A": "gemini-2.0-flash",
    "B": "gemma3:27b",
    "C": "deepseek-r1:14b"
}

def get_summary(text):
    model_id = "A"
    pidx = 1

    model_name = models[model_id]
    prompt = prompts[pidx]
    template = templates[pidx]

    start_time = time.time()

    try:
        if model_id == "A":
            summary = chat_with_gemini(model_name, prompt, template, text)
        else:
            summary = chat_with_openai(model_name, prompt, template, text)

        elapsed_time = time.time() - start_time
        logger.info(f"Model {model_id}({model_name}) took {elapsed_time:.2f} seconds")

        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return f"Error generating summary: {e}"


def chat_with_gemini(model_name, prompt, template, message):
    try:
        # Configure the model
        load_dotenv()
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # Create the model instance
        model = genai.GenerativeModel(model_name)
        
        content = template.format(text=message)
        
        # Create a chat instance
        chat = model.start_chat(history=[])
        
        # Add system prompt
        chat.send_message(prompt)
        
        # Send the content and get response
        response = chat.send_message(content)
        
        summary = response.text.strip()
        
        # Handle </think> tag if present
        if '</think>' in summary:
            last_think_pos = summary.rindex('</think>')
            summary = summary[last_think_pos + 8:].lstrip()
            
        return summary
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def chat_with_openai(model_name, prompt, template, message):
    client = OpenAI(
        api_key='ollama',
        base_url='http://solarsuna.com:34567/v1'
    )
    
    try:
        content = template.format(text=message)
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=15000,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Handle </think> tag if present
        if '</think>' in summary:
            last_think_pos = summary.rindex('</think>')
            summary = summary[last_think_pos + 8:].lstrip()
            
        return summary
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"
