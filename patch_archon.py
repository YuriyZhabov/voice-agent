import re

filepath = r'D:\Project\archon\python\src\server\services\llm_provider_service.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''        if provider_name == "openai":
            if api_key:
                client = openai.AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI client created successfully")'''

new = '''        if provider_name == "openai":
            if api_key:
                if base_url:
                    client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
                    logger.info(f"OpenAI client created with base_url: {base_url}")
                else:
                    client = openai.AsyncOpenAI(api_key=api_key)
                    logger.info("OpenAI client created successfully")'''

content = content.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patched successfully')
