import json
import os
import re
import sys

import requests

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_ID = "prism-ml/bonsai-27b"
MAX_TOKENS = 16384

def ask_model(system_prompt, user_prompt):
    data = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": MAX_TOKENS,
        "stream": True
    }

    try:
        print("[Tech Lead -> Bonsai 27B] Gorev gonderiliyor (Stream aktif)...")
        print(f"  Prompt (ilk 80 karakter): {user_prompt[:80]}...")

        response = requests.post(LM_STUDIO_URL, json=data, stream=True, timeout=(15, None))
        if response.status_code != 200:
            print(f"[HATA] HTTP {response.status_code}: {response.text}")
            sys.exit(1)

        content_parts = []
        reasoning_parts = []
        token_count = 0

        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode('utf-8') if isinstance(raw_line, bytes) else raw_line
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})

                    reasoning_chunk = delta.get("reasoning_content") or delta.get("reasoning") or ""
                    content_chunk = delta.get("content") or ""

                    if reasoning_chunk:
                        reasoning_parts.append(reasoning_chunk)
                    if content_chunk:
                        content_parts.append(content_chunk)

                    token_count += 1
                    if token_count % 100 == 0:
                        sys.stdout.write(f"\r  [Bonsai 27B Uretim] {token_count} token uretildi...")
                        sys.stdout.flush()
                except Exception:
                    pass

        print(f"\r  [Bonsai 27B Uretim] Toplam {token_count} token basariyla alindi.  ")
        full_content = "".join(content_parts)
        full_reasoning = "".join(reasoning_parts)

        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": full_content,
                    "reasoning_content": full_reasoning
                }
            }],
            "usage": {
                "total_tokens": token_count
            }
        }
    except Exception as e:
        print(f"[HATA] Model'e ulasilamadi: {e}")
        sys.exit(1)

def extract_code(result):
    """Model cevabindan Python kodunu cikarir."""
    message = result.get('choices', [{}])[0].get('message', {})
    content = message.get('content', '')

    # Bazi modeller thinking/reasoning icin ayri alan kullanir
    if not content.strip():
        content = message.get('reasoning_content', '')

    if not content.strip():
        return None

    # ```python ... ``` blogu ara
    code_match = re.search(r'```(?:python)?\s*\n(.*?)```', content, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    # ``` ... ``` blogu ara (dil belirtilmeden)
    code_match = re.search(r'```\s*\n(.*?)```', content, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    # Hic code block yoksa, import veya def ile baslayan satirlari al
    lines = content.strip().split('\n')
    if lines and (lines[0].startswith('import ') or lines[0].startswith('from ') or lines[0].startswith('def ') or lines[0].startswith('class ')):
        return content.strip()

    return None

SYSTEM_PROMPT = """You are an expert Python developer. You write clean, production-ready Python code.

RULES:
1. Output ONLY a single Python code block wrapped in ```python and ```.
2. Do NOT include any explanation, commentary, or text outside the code block.
3. The code must be complete, full, and directly runnable.
4. Keep internal reasoning concise and directly proceed to generating the final code.
5. Follow PEP 8 style."""

def main():
    if len(sys.argv) < 3:
        print("Kullanim: python orchestrator.py <hedef_dosya> <istek>")
        sys.exit(1)

    target_file = sys.argv[1]
    user_request = sys.argv[2]

    full_prompt = user_request
    if os.path.exists(target_file):
        try:
            with open(target_file, encoding='utf-8') as f:
                existing_code = f.read()
            if existing_code.strip():
                full_prompt += f"\n\nHere is the current existing code in {target_file}. Update it with the requested changes, keeping all existing imports, methods, and structure intact:\n```python\n{existing_code}\n```"
        except Exception:
            pass

    result = ask_model(SYSTEM_PROMPT, full_prompt)

    # Debug kaydi
    with open("last_debug.json", "w", encoding="utf-8") as df:
        json.dump(result, df, ensure_ascii=False, indent=2)

    code = extract_code(result)

    if code:
        dirname = os.path.dirname(target_file)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"[BASARILI] Kod yazildi: {target_file} ({len(code)} byte)")
    else:
        # Hata durumunda ham cevabi goster
        message = result.get('choices', [{}])[0].get('message', {})
        content = message.get('content', '')[:200]
        reasoning = message.get('reasoning_content', '')[:200]
        print("[HATA] Kod cikarilamamdi.")
        print(f"  content: {content}")
        print(f"  reasoning: {reasoning}")
        sys.exit(1)

if __name__ == "__main__":
    main()
