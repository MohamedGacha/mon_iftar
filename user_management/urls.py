from django.urls import path

from .views import (
    AddBeneficiaireAPIView,
    BeneficiaireListAPIView,
    BeneficiaireSearchAPIView,
    BenevoleListAPIView,
    CreateBenevoleAPIView,
    CreateLocationAPIView,
    CurrentUserAPIView,
    DeleteBeneficiaireAPIView,
    LocationListAPIView,
    MakeAdminAPIView,
    SearchLocationAPIView,
)

urlpatterns = [
    path('benevole/create/', CreateBenevoleAPIView.as_view(), name='create-benevole'),
    path('benevole/make-admin/', MakeAdminAPIView.as_view(), name='make-admin'),
    path('beneficiaire/add/', AddBeneficiaireAPIView.as_view(),
         name='add-beneficiaire'),
    path('beneficiaire/delete/', DeleteBeneficiaireAPIView.as_view(),
         name='delete-beneficiaire'),
    path('locations/', LocationListAPIView.as_view(), name='location-list'),
    path('benevoles/', BenevoleListAPIView.as_view(), name='benevole-list'),
    path('beneficiaires/', BeneficiaireListAPIView.as_view(),
         name='beneficiaire-list'),
    path('beneficiaire/search/', BeneficiaireSearchAPIView.as_view(),
         name='beneficiaire-search'),
    path('location/create/', CreateLocationAPIView.as_view(), name='create-location'),
    path('location/search/', SearchLocationAPIView.as_view(), name='search-location'),
     path('me/', CurrentUserAPIView.as_view(), name='current-user'),
]
