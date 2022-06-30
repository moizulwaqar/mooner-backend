from .crypto_integrations import *
from django.urls import path
from .views import *
from .wallet_admin import *

urlpatterns = [
    path('wallet/', UserWallet.as_view()),
    path('crypto_wallet/', CryptoWallet.as_view()),
    path('sharecrypto_token/', ShareCryptoTokens.as_view()),
    path('load_mnr/', LoadMNR.as_view()),
    path('connect_account/', ConnectAccount.as_view()),
    path('external_bank/', ExternalBank.as_view()),

    # wallet_admin
    path('kyc_approved_documents/', GetKYCApprovedDocument.as_view()),
    path('kyc_pending_documents/', GetKYCPendingDocument.as_view()),
    path('kyc_request_documents/', GetKYCRequest.as_view()),
    path('send_tokens/', SendTokens.as_view()),
    path('admin_token_history/', AdminTokenHistory.as_view()),
    path('admin_wallet_dashboard/', AdminWalletDashboard.as_view()),

    path('all_attached_bank/', BankAccounts.as_view()),
    path('transfer_amount/', TransferAmount.as_view()),
    path('payout/', AmountPayout.as_view()),
    path('payout_list/', PayoutList.as_view()),
    path('delete_bank/', DeleteExternalBank.as_view()),
    path('delete_bank/', DeleteExternalBank.as_view()),
    path('set_token_price/', SetTokenPrice.as_view()),
    path('update_token_price/<int:pk>/', UpdateTokenPrice.as_view()),
    path('commision_history/', CommisionHistory.as_view())

]
