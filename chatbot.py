from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from services.ai_service import AIService
from models.chat import ChatConversation
from datetime import datetime
import traceback
import sys

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/ai-chat")
@login_required
def index():
    conv_id = request.args.get("conv", "")
    user_id = session["user_id"]
    conversations = ChatConversation.find_by_user(user_id)
    convs_data = [c.to_dict() for c in conversations]

    current_conv = None
    if conv_id:
        current_conv = ChatConversation.find_by_id(conv_id)
        if current_conv and current_conv.user_id != user_id:
            current_conv = None

    if not current_conv and convs_data:
        current_conv = conversations[0]
    elif not current_conv:
        current_conv = ChatConversation({
            "user_id": user_id,
            "title": "New Chat",
            "district": session.get("district", ""),
            "messages": [],
        })
        current_conv.save()

    return render_template(
        "ai_chat.html",
        lang=session.get("lang", "en"),
        conversations=convs_data,
        current_conv=current_conv.to_dict() if current_conv else None,
        selected_district=session.get("district", ""),
    )

@chatbot_bp.route("/api/chat/send", methods=["POST"])
@login_required
def chat_send():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request payload"}), 400

        message = data.get("message", "").strip()
        conv_id = data.get("conversation_id", "")
        language = data.get("language", session.get("lang", "en"))
        district = data.get("district", session.get("district", ""))
        user_id = session["user_id"]

        if not message:
            msg = "Please enter a question." if language == "en" else "தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்."
            return jsonify({"success": False, "message": msg})

        if len(message) < 2:
            msg = "Question too short. Please be more specific." if language == "en" else "கேள்வி மிகவும் குறுகியது. மேலும் விவரமாக கேளுங்கள்."
            return jsonify({"success": False, "message": msg})

        ai_service = AIService()

        conv = None
        history = []
        if conv_id:
            conv = ChatConversation.find_by_id(conv_id)
            if conv and conv.user_id == user_id:
                history = [{"role": m["role"], "content": m["content"]} for m in conv.messages]

        response = ai_service.get_response(
            message=message,
            language=language,
            district=district,
            history=history,
        )

        if not conv:
            conv = ChatConversation({
                "user_id": user_id,
                "title": message[:60] + ("..." if len(message) > 60 else ""),
                "district": district,
                "messages": [],
            })
            conv.save()
        elif conv.title in ("New Chat", "", None):
            title = message.strip()[:60]
            if len(message.strip()) > 60:
                title += "..."
            conv.title = title
            conv.update({"title": conv.title})

        conv.add_message("user", message)
        conv.add_message("assistant", response)

        return jsonify({
            "success": True,
            "reply": response,
            "conversation_id": conv.id,
            "title": conv.title,
        })

    except Exception as e:
        import sys
        print(f"[Chat Error] {traceback.format_exc()}", file=sys.stderr)
        lang = session.get("lang", "en")
        msg = "Unable to contact the AI service at the moment. Please try again later."
        return jsonify({"success": False, "message": msg}), 500

@chatbot_bp.route("/api/chat/conversations", methods=["GET"])
@login_required
def list_conversations():
    try:
        user_id = session["user_id"]
        conversations = ChatConversation.find_by_user(user_id)
        return jsonify({"success": True, "conversations": [c.to_dict() for c in conversations]})
    except Exception as e:
        print(f"[Chat Error] list_conversations: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to load conversations"}), 500

@chatbot_bp.route("/api/chat/conversation/<conv_id>", methods=["GET"])
@login_required
def get_conversation(conv_id):
    try:
        user_id = session["user_id"]
        conv = ChatConversation.find_by_id(conv_id)
        if not conv or conv.user_id != user_id:
            lang = session.get("lang", "en")
            msg = "Conversation not found." if lang == "en" else "உரையாடல் கிடைக்கவில்லை."
            return jsonify({"success": False, "message": msg}), 404
        return jsonify({"success": True, "conversation": conv.to_dict()})
    except Exception as e:
        print(f"[Chat Error] get_conversation: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to load conversation"}), 500

@chatbot_bp.route("/api/chat/conversation/<conv_id>", methods=["DELETE"])
@login_required
def delete_conversation(conv_id):
    try:
        user_id = session["user_id"]
        conv = ChatConversation.find_by_id(conv_id)
        if not conv or conv.user_id != user_id:
            lang = session.get("lang", "en")
            msg = "Conversation not found." if lang == "en" else "உரையாடல் கிடைக்கவில்லை."
            return jsonify({"success": False, "message": msg}), 404
        ChatConversation.delete_by_id(conv_id)
        return jsonify({"success": True})
    except Exception as e:
        print(f"[Chat Error] delete_conversation: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to delete conversation"}), 500

@chatbot_bp.route("/api/chat/new", methods=["POST"])
@login_required
def new_conversation():
    try:
        user_id = session["user_id"]
        district = session.get("district", "")
        conv = ChatConversation({
            "user_id": user_id,
            "title": "New Chat",
            "district": district,
            "messages": [],
        })
        conv.save()
        return jsonify({"success": True, "conversation": conv.to_dict()})
    except Exception as e:
        print(f"[Chat Error] new_conversation: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to create conversation"}), 500

@chatbot_bp.route("/api/chat/export", methods=["POST"])
@login_required
def export_chat():
    try:
        data = request.get_json()
        conv_id = data.get("conv_id", "")
        export_format = data.get("format", "txt")
        lang = session.get("lang", "en")
        user_id = session["user_id"]

        conv = ChatConversation.find_by_id(conv_id)
        if not conv or conv.user_id != user_id:
            msg = "Conversation not found." if lang == "en" else "உரையாடல் கிடைக்கவில்லை."
            return jsonify({"success": False, "message": msg}), 404

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        lang_label = "Tamil" if lang == "ta" else "English"

        if export_format == "pdf":
            from fpdf import FPDF
            from fpdf.enums import XPos, YPos
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
            pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf")
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, text="AI Agriculture Assistant - Chat Export", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, text=f"Date: {now}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 6, text=f"District: {conv.district or 'Not set'}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 6, text=f"Language: {lang_label}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
            pdf.ln(6)

            pdf.set_font("Arial", "", 11)
            for msg in conv.messages:
                role = "You" if msg["role"] == "user" else "AI Assistant"
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Arial", "B", 11)
                pdf.multi_cell(0, 6, text=f"[{role}]")
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Arial", "", 11)
                pdf.multi_cell(0, 6, text=msg.get("content", ""))
                pdf.set_x(pdf.l_margin)
                pdf.ln(3)

            pdf_output = bytes(pdf.output())
            import base64
            return jsonify({
                "success": True,
                "export": base64.b64encode(pdf_output).decode("ascii"),
                "filename": f"chat_{conv_id[:8]}.pdf",
                "mime": "application/pdf",
                "encoding": "base64",
            })
        else:
            lines = []
            header = (
                f"AI Agriculture Assistant - Chat Export\n"
                f"Date: {now}\n"
                f"District: {conv.district or 'Not set'}\n"
                f"Language: {lang_label}\n"
                f"{'=' * 50}\n\n"
            )
            lines.append(header)

            for msg in conv.messages:
                role = "You" if msg["role"] == "user" else "AI Assistant"
                lines.append(f"[{role}]\n{msg['content']}\n\n")

            return jsonify({
                "success": True,
                "export": "".join(lines),
                "filename": f"chat_{conv_id[:8]}.txt",
                "mime": "text/plain",
            })
    except Exception as e:
        print(f"[Chat Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to export chat"}), 500
