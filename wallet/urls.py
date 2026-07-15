from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    user_login_page_view,
    user_dashboard_template_view,
    admin_dashboard_template_view,
    user_logout_view,
    DualLoginView,
    DepositView,
    TransferView,
    ExchangeView
)
from .admin_views import (
    AdminDashboardStatsView,
    AdminGlobalTransactionsView,
    AdminExchangeRateView
)


urlpatterns = [
    # --- صفحات واجهات العرض (HTML Templates with Session Guard) ---
    path('login', user_login_page_view, name='user_login_page'),
    path('dashboard', user_dashboard_template_view, name='user_dashboard_luminous'),
    path('admin-dashboard', admin_dashboard_template_view, name='admin_dashboard_luminous'),
    path('logout', user_logout_view, name='user_logout_action'),

    # --- واجهة تسجيل الدخول والتوكنات الموحدة (APIs) ---
    path('auth/login', DualLoginView.as_view(), name='dual_login_api'),
    path('auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh_api'),

    # --- واجهات العمليات المالية للعملاء (تتطلب JWT Bearer Token) ---
    path('deposit', DepositView.as_view(), name='wallet_deposit_api'),
    path('transfer', TransferView.as_view(), name='wallet_transfer_api'),
    path('exchange', ExchangeView.as_view(), name='wallet_exchange_api'),

    # --- واجهات لوحة تحكم المسؤول (الأدمن) ---
    path('admin/stats', AdminDashboardStatsView.as_view(), name='admin_stats_api'),
    path('admin/transactions', AdminGlobalTransactionsView.as_view(), name='admin_transactions_api'),
    path('admin/exchange-rates', AdminExchangeRateView.as_view(), name='admin_exchange_rates_api'),
]