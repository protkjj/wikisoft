"""
WIKISOFT 5 Telegram Bot

실행: python -m tg_bot.bot
"""

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from tg_bot.config import config
from tg_bot.handlers import (
    start,
    help_command,
    check_status,
    recent_results,
    button_callback,
    handle_message,
)

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    """봇 시작"""
    logger.info("WIKISOFT 5 Telegram Bot 시작...")

    # 필수 설정 확인 (봇 토큰)
    config.validate()
    logger.info("WIKISOFT4 백엔드: %s", config.api_base_url)

    # Application 생성
    app = Application.builder().token(config.bot_token).build()

    # 명령어 핸들러 등록
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("check", check_status))
    app.add_handler(CommandHandler("recent", recent_results))

    # 콜백 쿼리 핸들러 (인라인 버튼)
    app.add_handler(CallbackQueryHandler(button_callback))

    # 일반 메시지 핸들러
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 봇 실행
    logger.info("봇이 실행 중입니다. Ctrl+C로 종료하세요.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
