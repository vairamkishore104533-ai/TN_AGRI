import os

class AIService:
    MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self._client = None
        self._import_error = None
        if self.api_key:
            print(f"[AIService] Groq API key loaded ({self.api_key[:3]}...{self.api_key[-4:]}). Model: {self.MODEL}", flush=True)
        else:
            print("[AIService] No GROQ_API_KEY set in .env", flush=True)
        try:
            from groq import Groq
            self._Groq = Groq
            print(f"[AIService] Groq SDK imported successfully", flush=True)
        except ImportError as e:
            self._import_error = f"Groq SDK not installed: {e}"
            print(f"[AIService] {self._import_error}", flush=True)
        except Exception as e:
            self._import_error = f"Groq SDK import error: {e}"
            print(f"[AIService] {self._import_error}", flush=True)

    def _get_client(self):
        if self._import_error:
            raise RuntimeError(self._import_error)
        if self._client is None:
            self._client = self._Groq(api_key=self.api_key)
        return self._client

    def get_response(self, message, language="en", district="", history=None):
        if not self.api_key:
            return "AI service is not configured. Please set GROQ_API_KEY in .env file."

        if self._import_error:
            return f"Groq SDK import failed: {self._import_error}"

        system_prompt = self._build_system_prompt(language, district)

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history[-20:]:
                role = "assistant" if msg["role"] == "assistant" else "user"
                messages.append({"role": role, "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        try:
            print(f"[AIService] Sending request to Groq model={self.MODEL} messages={len(messages)}", flush=True)
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                top_p=0.95,
            )

            result = response.choices[0].message.content
            if not result or not result.strip():
                print(f"[AIService] Groq returned empty response", flush=True)
                return "The AI service returned an empty response. Please try again."

            print(f"[AIService] Groq response OK ({len(result)} chars)", flush=True)
            return result.strip()

        except Exception as e:
            import traceback
            print(f"[AIService] Groq API call failed: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()
            err_str = str(e).lower()
            if "401" in err_str or "unauthorized" in err_str or "invalid api key" in err_str:
                return ("AI service configuration error: Invalid or unauthorized Groq API key. "
                        "Please check your GROQ_API_KEY in .env file.")
            if "429" in err_str or "rate limit" in err_str:
                return "AI service is currently overloaded (rate limited). Please wait and try again."
            if "timeout" in err_str or "timed out" in err_str:
                return "AI service request timed out. Please try again."
            return f"AI service error: {type(e).__name__}: {str(e)}"

    def _build_system_prompt(self, language, district=""):
        lang_instruction = (
            "Reply only in Tamil language. Use Tamil agricultural terminology."
            if language == "ta"
            else "Reply only in English."
        )

        district_context = ""
        if district:
            zone, info = self._get_zone_info(district)
            if info:
                crops = ", ".join(info.get("crops", info.get("major_crops", "").split(",")[:3]))
                crops = crops[:200]
                soil = info.get("soil", "")
                climate = info.get("climate", "")
                name_ta = info.get("name_ta", zone)
                zone_name = name_ta if language == "ta" else zone

                if language == "ta":
                    district_context = (
                        f"பயனர் {district} மாவட்டத்தைச் சேர்ந்தவர். "
                        f"இந்த மாவட்டம் {zone_name} மண்டலத்தில் உள்ளது. "
                        f"மண் வகை: {soil}. காலநிலை: {climate}. முக்கிய பயிர்கள்: {crops}. "
                        f"இந்த சூழலுக்கு ஏற்ப ஆலோசனைகளை வழங்கவும்."
                    )
                else:
                    district_context = (
                        f"The user is from {district} district ({zone_name} zone). "
                        f"Soil: {soil}. Climate: {climate}. Major crops: {crops}. "
                        f"Tailor your advice to this context."
                    )

        return (
            f"You are an expert AI Agriculture Assistant specialized in Tamil Nadu farming.\n\n"
            f"{lang_instruction}\n\n"
            f"Guidelines:\n"
            f"- Answer ONLY agriculture and farming related questions.\n"
            f"- If the user asks about non-agriculture topics (politics, entertainment, technology, general news, etc.), "
            f"politely refuse by saying you are designed only for agriculture assistance.\n"
            f"- Use the user's district and agro-climatic zone whenever relevant.\n"
            f"- Be practical, farmer-friendly and accurate.\n"
            f"- Use Markdown formatting for clarity: **bold** for emphasis, bullet points for lists, "
            f"headings for sections, and code blocks where appropriate.\n"
            f"- Keep responses well-structured but concise.\n"
            f"{district_context}"
        )

    def _get_zone_info(self, district):
        ZONE_INFO = {
            "Cauvery Delta Zone": {"soil": "Alluvial, Clay", "climate": "Tropical, 25-37°C, 900-1100mm rain", "crops": ["Paddy", "Sugarcane", "Banana", "Coconut"]},
            "North Eastern Zone": {"soil": "Red Sandy Loam, Clay Loam", "climate": "Sub-tropical, 22-35°C, 900-1200mm rain", "crops": ["Paddy", "Groundnut", "Sugarcane", "Vegetables", "Mango"]},
            "Western Zone": {"soil": "Red Loam, Black Soil", "climate": "Semi-arid, 20-38°C, 600-800mm rain", "crops": ["Coconut", "Cotton", "Turmeric", "Banana", "Vegetables"]},
            "Southern Zone": {"soil": "Red Sandy, Black, Coastal Alluvium", "climate": "Semi-arid to Dry, 22-36°C, 700-900mm rain", "crops": ["Cotton", "Paddy", "Groundnut", "Chilli", "Pulses"]},
            "Hilly Zone": {"soil": "Red Loamy, Laterite, Forest Soil", "climate": "Cool, 12-25°C, 1200-2000mm rain", "crops": ["Tea", "Coffee", "Spices", "Vegetables", "Fruits"]},
            "High Rainfall Zone": {"soil": "Deep Red Loam, Coastal Alluvium", "climate": "Tropical, 24-34°C, 1500-2500mm rain", "crops": ["Coconut", "Rubber", "Pepper", "Cloves", "Banana"]},
        }
        DISTRICT_ZONES = {
            "Cauvery Delta Zone": ["Thanjavur", "Tiruvarur", "Nagapattinam", "Mayiladuthurai"],
            "North Eastern Zone": ["Chennai", "Chengalpattu", "Kancheepuram", "Tiruvallur", "Cuddalore", "Villupuram", "Kallakurichi", "Vellore", "Ranipet", "Tirupattur", "Tiruvannamalai"],
            "Western Zone": ["Coimbatore", "Tiruppur", "Erode", "Karur", "Namakkal", "Dindigul", "Theni"],
            "Southern Zone": ["Madurai", "Virudhunagar", "Thoothukudi", "Tirunelveli", "Tenkasi", "Sivaganga", "Ramanathapuram", "Pudukkottai"],
            "Hilly Zone": ["Nilgiris"],
            "High Rainfall Zone": ["Kanniyakumari"],
        }
        ALL_DISTRICTS = [
            "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
            "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram",
            "Kanniyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
            "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
            "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
            "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
            "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
            "Vellore", "Villupuram", "Virudhunagar",
        ]

        if district not in ALL_DISTRICTS:
            return None, None

        for zone, districts in DISTRICT_ZONES.items():
            if district in districts:
                return zone, ZONE_INFO.get(zone)

        for zone, districts in {
            "Cauvery Delta Zone": ["Ariyalur", "Perambalur", "Tiruchirappalli"],
            "North Eastern Zone": ["Dharmapuri", "Krishnagiri", "Salem"],
            "Southern Zone": ["Thoothukudi", "Tirunelveli"],
        }.items():
            if district in districts:
                return zone, ZONE_INFO.get(zone)

        return None, None
