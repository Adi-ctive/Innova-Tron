from django.contrib import admin
from django.urls import path, include
from .views import SignupView, LoginView, AIProcessingView, SpeechToTextView, TranslateView

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/ai-processing/', AIProcessingView.as_view(), name='ai-processing'),
    path('api/speech-to-text/', SpeechToTextView.as_view(), name='speech-to-text'),
    path('api/translate/', TranslateView.as_view(), name='translate'),
]

