from aiogram import Router
from .start import router as start_router
from .searches import router as searches_router
from .stats import router as stats_router
from .export import router as export_router
from .favorites import router as favorites_router
from .user_settings import router as settings_router
from .admin import router as admin_router

main_router = Router()
main_router.include_router(start_router)
main_router.include_router(searches_router)
main_router.include_router(stats_router)
main_router.include_router(export_router)
main_router.include_router(favorites_router)
main_router.include_router(settings_router)
main_router.include_router(admin_router)
