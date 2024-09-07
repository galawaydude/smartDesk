from django.contrib import admin
from django.urls import path
from accounts import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('verify-registration/', views.verify_registration, name='verify_registration'),
    path('login/', views.login_view, name='login'),
    path('verify-login/', views.verify_login, name='verify_login'),
    path('login-success/', views.login_success, name='login_success'),
    path('hr-chatbot/', views.hr_chatbot_view, name='hr_chatbot'),
    path('hr-chatbot-page/', views.hr_chatbot_page, name='hr_chatbot_page'),
    path('upload-document/', views.upload_document, name='upload_document'),
path('document-chat/', views.document_chat, name='document_chat'),
path('document-chat-page/', views.document_chat_page, name='document_chat_page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)