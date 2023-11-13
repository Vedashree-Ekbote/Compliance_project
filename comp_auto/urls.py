from django.contrib import admin
from django.urls import path
from comp_auto import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", views.index,name='form'),
    path('register/', views.register, name='register'),
    path('login/',views.login_view,name='login'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('genreport/', views.genreport, name='genreport'),
    path('myreport/', views.myreport, name='myreport'),
    path('audit_questions/',views.audit_questions,name='audit_questions'),
    path('logout/', views.logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
