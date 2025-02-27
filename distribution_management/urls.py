from django.urls import path

from .views import (
    CreateDistributionView,
    DistributionListBeneficiaireListAPIView,
    DistributionListLocationAPIView,
    QRCodeScanView,
    TodayDistributionAPIView,
    UpcomingDistributionAPIView,
)

urlpatterns = [
    # API for creating a new distribution
    path('distributions/create/', CreateDistributionView.as_view(),
         name='create-distribution'),

    # API for getting beneficiaries in a specific distribution list
    path('distributions/<int:distribution_list_id>/beneficiaries/',
         DistributionListBeneficiaireListAPIView.as_view(), name='distribution-list-beneficiaries'),

    # API for scanning a QR code and validating it
    path('qr-code/scan/', QRCodeScanView.as_view(), name='qr-code-scan'),

    # API for getting distribution lists for a specific location with benevoles
    path('distributions/location/<int:location_id>/',
         DistributionListLocationAPIView.as_view(), name='distribution-list-location'),

    # API for listing all distributions happening today
    path('distributions/today/', TodayDistributionAPIView.as_view(),
         name='today-distributions'),

    # API for listing all upcoming distributions
    path('distributions/upcoming/', UpcomingDistributionAPIView.as_view(),
         name='upcoming-distributions'),
]
