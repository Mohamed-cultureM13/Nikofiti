from django.urls import path
from . import views

urlpatterns = [
    path('whatsapp-webhook/', views.whatsAppWebhook, name='whatsapp_webhook'),
]

#webhook url
#https://fidelio36.pythonanywhere.com/whatsapp-webhook/  #for python-anywhere

#token - kwa ajili ya testing, nitatengeneza nyingine wakati wa production kabla ya kudeploy.
# 6ab1d155-e097-4dde-bf4d-8093efb4d503

