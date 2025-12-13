from django.urls import path
from detector import views

urlpatterns = [
    # Landing and Authentication
    path('', views.landing_page, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('delete/', views.delete_account, name='delete_account'),
    
    # Dashboard and Gmail
    path('dashboard/', views.dashboard, name='dashboard'),
    path('connect-gmail/', views.connect_gmail, name='connect_gmail'),
    path('disconnect-gmail/', views.disconnect_gmail, name='disconnect_gmail'),
    
    # Email Management
    path('emails/', views.email_list, name='email_list'),
    path('emails/<int:email_id>/', views.email_detail, name='email_detail'),
    
    # API Endpoints
    path('api/scan/', views.start_scan, name='start_scan'),

    # Debug Endpoints 
    path('api/debug/email-count/', views.debug_email_count, name='debug_email_count'),
    path('api/debug/last-scan/', views.debug_last_scan, name='debug_last_scan'),
]
