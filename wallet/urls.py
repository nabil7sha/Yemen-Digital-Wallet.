from django.urls import path
from .views import ProfileView, TransactionListView, DepositView, TransferView, ExchangeView
from .admin_views import AdminDashboardStatsView, AdminGlobalTransactionsView

urlpatterns = [
    # --- وحدة العميل المالي (Client Wallet API - مفتوحة وبدون أمان للعرض المباشر) ---
    path('profile', ProfileView.as_view(), name='user_profile_no_auth'),
    path('transactions', TransactionListView.as_view(), name='transaction_list_no_auth'),
    path('deposit', DepositView.as_view(), name='wallet_deposit_no_auth'),
    path('transfer', TransferView.as_view(), name='wallet_transfer_no_auth'),
    path('exchange', ExchangeView.as_view(), name='wallet_exchange_no_auth'),

    # --- وحدة الرقابة الإدارية (Admin Controller API - مفتوحة للعرض) ---
    path('admin/stats', AdminDashboardStatsView.as_view(), name='admin_stats'),
    path('admin/transactions', AdminGlobalTransactionsView.as_view(), name='admin_transactions_list'),
]