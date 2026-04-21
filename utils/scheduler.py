# import asyncio
# import logging
# from services.notification_service import NotificationService
#
# logger = logging.getLogger(__name__)
#
# notification_service = NotificationService()
#
#
# async def scheduler(bot):
#     while True:
#         try:
#             await asyncio.sleep(86400)  # 24 часа
#
#             await notification_service.send_daily_notifications(bot)
#
#         except Exception as e:
#             logger.error(f"Ошибка в планировщике: {e}")