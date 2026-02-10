"""
Telegram Bot 명령어 핸들러
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - 봇 시작
    """
    keyboard = [
        [InlineKeyboardButton("📋 검증 시작", callback_data="start_validation")],
        [InlineKeyboardButton("📊 최근 결과", callback_data="recent_results")],
        [InlineKeyboardButton("❓ 도움말", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 <b>WIKISOFT 5</b>에 오신 것을 환영합니다!\n\n"
        "퇴직연금 명부 검증을 도와드립니다.\n"
        "아래 버튼을 선택하세요.",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help - 도움말
    """
    help_text = """
<b>📖 WIKISOFT 5 사용법</b>

<b>명령어:</b>
/start - 봇 시작
/check - 검증 상태 확인
/recent - 최근 검증 결과
/help - 이 도움말

<b>검증 방법:</b>
1. Excel에서 명부 작성
2. AI 수식으로 검증 실행
3. 여기서 결과 알림 수신

<b>문의:</b>
문제가 있으면 관리자에게 연락하세요.
"""
    await update.message.reply_text(help_text, parse_mode="HTML")


async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /check - 검증 상태 확인
    """
    # TODO: 실제 검증 상태 조회 로직
    await update.message.reply_text(
        "📊 <b>검증 상태</b>\n\n"
        "현재 진행 중인 검증이 없습니다.\n"
        "Excel에서 검증을 시작하세요.",
        parse_mode="HTML",
    )


async def recent_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /recent - 최근 검증 결과
    """
    # TODO: 실제 결과 조회 로직
    await update.message.reply_text(
        "📋 <b>최근 검증 결과</b>\n\n"
        "아직 검증 이력이 없습니다.",
        parse_mode="HTML",
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    인라인 버튼 콜백 처리
    """
    query = update.callback_query
    await query.answer()

    if query.data == "start_validation":
        await query.edit_message_text(
            "📋 <b>검증 시작</b>\n\n"
            "1. Excel 템플릿을 열어주세요\n"
            "2. 명부 데이터를 입력하세요\n"
            "3. AI 검증 수식을 실행하세요\n\n"
            "검증이 완료되면 여기로 알림이 옵니다.",
            parse_mode="HTML",
        )

    elif query.data == "recent_results":
        await query.edit_message_text(
            "📋 <b>최근 검증 결과</b>\n\n"
            "아직 검증 이력이 없습니다.",
            parse_mode="HTML",
        )

    elif query.data == "help":
        await query.edit_message_text(
            "<b>📖 도움말</b>\n\n"
            "/start - 봇 시작\n"
            "/check - 검증 상태\n"
            "/recent - 최근 결과\n"
            "/help - 도움말",
            parse_mode="HTML",
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    일반 메시지 처리 (자연어 대화)
    """
    text = update.message.text

    # 간단한 키워드 응답
    if "검증" in text:
        await update.message.reply_text(
            "검증을 시작하려면 /start 를 입력하세요."
        )
    elif "도움" in text or "help" in text.lower():
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "무엇을 도와드릴까요?\n"
            "/help 로 사용법을 확인하세요."
        )
