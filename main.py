import os
import json
import base64
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai
from prompt_templates import SYSTEM_PROMPT, FEEDBACK_SYSTEM_PROMPT

app = FastAPI(title="Mii Craftsman API", description="トモコレ Mii職人 AI Back-end API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Mii Craftsman Backend"}

@app.get("/api/parts")
def get_parts_catalog():
    catalog_path = os.path.join(os.path.dirname(__file__), "parts_catalog.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/analyze")
async def analyze_photo(
    file: UploadFile = File(...),
    style: str = Form("そっくり重視"),
    target_person: str = Form("正面の人物")
):
    try:
        contents = await file.read()
        encoded_image = base64.b64encode(contents).decode("utf-8")
        
        if not GEMINI_API_KEY:
            # Mock fallback response for offline testing
            return {
                "target_description": f"{target_person}の分析完了",
                "style_preference": style,
                "recipe": {
                    "contour": {"code": "K-1-2", "name": "輪郭 1段目・2番目", "adjustments": "標準", "notes": "あごがとがった卵型・シャープ"},
                    "skin_color": "上から2段目の透明感ある肌色",
                    "hair": {
                        "type": "custom_combo",
                        "fringe": {"code": "F-12-3", "name": "前髪 12段目・3番目", "description": "シースルーぱっつん"},
                        "back": {"code": "B-3-2", "name": "後髪 3段目・2番目", "description": "丸いボブ"},
                        "color": "ライトアッシュブラウン"
                    },
                    "eyebrows": {"code": "E-3-5", "adjustments": "下へ1回"},
                    "eyes": {
                        "code": "Y-2-1",
                        "adjustments": "縮小1回",
                        "double_eyelid": "YD-1-2",
                        "iris": "YP-1-1"
                    },
                    "nose": {"code": "N-1-3", "adjustments": "標準"},
                    "mouth": {"code": "M-6-2", "lipstick": "オフ", "adjustments": "標準"},
                    "ears": {"code": "R-1-2"},
                    "details": [
                        {"type": "D6 (ほくろ)", "adjustments": "1つ追加、下唇の右下へ移動"}
                    ]
                },
                "key_points": [
                    "重めマッシュ×シースルー前髪（F-12-3）で今風の雰囲気を再現",
                    "シャープな卵型輪郭（K-1-2）ですっきりフェイスライン",
                    "下唇の右下にホクロを追加して本人らしさUP"
                ],
                "full_text_response": "### 🎨 Miiレシピ提案\n写真から特徴を分析し、パーツ図鑑の番号をもとに最高精度のレシピを作成しました！"
            }
        
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)
        prompt = f"この写真の人物（{target_person}）のMiiレシピを作成してください。スタイル希望: {style}"
        
        response = model.generate_content([
            prompt,
            {"mime_type": file.content_type, "data": contents}
        ])
        
        # Parse JSON from AI output
        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != 0:
            result_json = json.loads(text[start:end])
            return result_json
        else:
            return {"full_text_response": text}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
