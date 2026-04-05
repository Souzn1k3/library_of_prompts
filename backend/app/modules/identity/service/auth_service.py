from app.config import Settings
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.identity.repository.refresh_token_repository import RefreshTokenRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.auth_logout_mixin import AuthLogoutMixin
from app.modules.identity.service.auth_refresh_mixin import AuthRefreshMixin
from app.modules.identity.service.auth_register_login_mixin import AuthRegisterLoginMixin
from app.modules.identity.service.auth_session_mixin import AuthSessionMixin
from app.modules.identity.service.display_name_policy import DisplayNamePolicy


class AuthService(AuthSessionMixin, AuthRegisterLoginMixin, AuthRefreshMixin, AuthLogoutMixin):
    def __init__(
        self,
        repo: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        settings: Settings,
        analytics: AnalyticsService | None = None,
        display_names: DisplayNamePolicy | None = None,
    ) -> None:
        self._repo = repo
        self._refresh_tokens = refresh_tokens
        self._settings = settings
        self._analytics = analytics
        self._display_names = display_names or DisplayNamePolicy()
