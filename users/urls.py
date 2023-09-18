from django.urls import path, include

from users.views import LoginView, VerificationTokenView, ProfileView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('verification/<pk>', VerificationTokenView.as_view(), name="Verification"),
    path('profile/', ProfileView.as_view(), name='profile'),

]
