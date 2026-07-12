from django.urls import path
from .views import (
    user_dashboard_template_view,       # دالة رندرة المستخدم بالـ Context
    admin_dashboard_template_view,      # دالة رندرة الأدمن بالـ Context
    ProfileView,
    TransactionListView,
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

    # --- واجهات العمليات المالية للعملاء (APIs) ---
    path('profile', ProfileView.as_view(), name='wallet_profile_api'),
    path('transactions', TransactionListView.as_view(), name='wallet_transactions_api'),
    path('deposit', DepositView.as_view(), name='wallet_deposit_api'),
    path('transfer', TransferView.as_view(), name='wallet_transfer_api'),
    path('exchange', ExchangeView.as_view(), name='wallet_exchange_api'),

    # --- واجهات لوحة التحكم للمشرفين والمسؤولين (Admin APIs) ---
    path('admin/stats', AdminDashboardStatsView.as_view(), name='admin_stats_api'),
    path('admin/transactions', AdminGlobalTransactionsView.as_view(), name='admin_transactions_api'),
    path('admin/exchange-rates', AdminExchangeRateView.as_view(), name='admin_exchange_rates_api'),
]