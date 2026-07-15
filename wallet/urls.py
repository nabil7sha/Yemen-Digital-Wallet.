from django.urls import path
from .views import (
    user_dashboard_template_view,       # دالة رندرة لوحة العميل (مؤمنة)
    admin_dashboard_template_view,      # دالة رندرة لوحة الإدارة (مؤمنة)
    custom_login_view,                  # دالة تسجيل دخول العميل
    custom_logout_view,                 # دالة تسجيل خروج العميل
    admin_login_view,                   # دالة تسجيل دخول الأدمن الجديدة 👈
    admin_logout_view,                  # دالة تسجيل خروج الأدمن الجديدة 👈
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
    # 🌐 مسارات رندرة الصفحات المباشرة مع الـ Context من الخادم (Server Rendered)
    path('dashboard', user_dashboard_template_view, name='user_dashboard_luminous'),
    path('admin-dashboard', admin_dashboard_template_view, name='admin_dashboard_luminous'),
    
    # 🔐 مسارات التوثيق والـ Auth للعملاء
    path('login', custom_login_view, name='user_login_luminous'),
    path('logout', custom_logout_view, name='user_logout_luminous'),

    # 🔐 مسارات التوثيق والـ Auth للإدارة (الأدمن) الجديدة 👈
    path('admin-login', admin_login_view, name='admin_login_luminous'),
    path('admin-logout', admin_logout_view, name='admin_logout_luminous'),

    # --- واجهات العمليات المالية للعملاء (APIs) ---
    path('deposit', DepositView.as_view(), name='wallet_deposit_api'),
    path('transfer', TransferView.as_view(), name='wallet_transfer_api'),
    path('exchange', ExchangeView.as_view(), name='wallet_exchange_api'),

    # --- واجهات لوحة التحكم للمشرفين والمسؤولين (Admin APIs) ---
    path('admin/stats', AdminDashboardStatsView.as_view(), name='admin_stats_api'),
    path('admin/transactions', AdminGlobalTransactionsView.as_view(), name='admin_transactions_api'),
    path('admin/exchange-rates', AdminExchangeRateView.as_view(), name='admin_exchange_rates_api'),
]