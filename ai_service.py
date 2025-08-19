# ai_service.py
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from config import LLM_MODEL, LLM_MAX_NEW_TOKENS, LLM_TEMPERATURE, LLM_TOP_K

_LLM = {"loaded": False, "ok": False, "err": None, "model": None, "tokenizer": None, "device": "cpu"}

def _ensure_llm():
    """在首次使用時載入 Flan-T5 模型與分詞器。"""
    if _LLM["loaded"]:
        return _LLM["ok"], _LLM["err"]
    _LLM["loaded"] = True

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 載入 T5 專用的分詞器和模型
        tokenizer = T5Tokenizer.from_pretrained(LLM_MODEL)
        model = T5ForConditionalGeneration.from_pretrained(LLM_MODEL).to(device)
        
        _LLM.update({"ok": True, "model": model, "tokenizer": tokenizer, "device": device})
        print(f"Flan-T5 model '{LLM_MODEL}' loaded successfully on {device}.")
        return True, None
    except Exception as e:
        _LLM["err"] = f"{e}"
        _LLM["ok"] = False
        return False, _LLM["err"]

def generate_ai_text(user_prompt: str) -> str:
    """使用已載入的 Flan-T5 模型生成文字回應。"""
    ok, err = _ensure_llm()
    if not ok:
        return f"🤖 AI 模型無法使用。\n詳細錯誤：{err}"

    tokenizer = _LLM["tokenizer"]
    model = _LLM["model"]
    device = _LLM["device"]

    # 為 Flan-T5 建立一個通用的問答指令
    input_text = f"請用繁體中文回答以下問題: {user_prompt}"

    try:
        input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                max_new_tokens=LLM_MAX_NEW_TOKENS,
                do_sample=True,
                temperature=LLM_TEMPERATURE,
                top_k=LLM_TOP_K
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.strip() or "（AI 沒有產生任何內容）"
    except Exception as e:
        return f"AI 產生內容時發生錯誤：{e}"
