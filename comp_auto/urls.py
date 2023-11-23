from django.contrib import admin
from django.urls import path
from comp_auto import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", views.index,name='form'),
    path('register/', views.register,name='register'),
    path('login/',views.login_view,name='login'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('genreport/', views.genreport, name='genreport'),
    path('myreport/', views.myreport, name='myreport'),
    path('audit_questions/',views.audit_questions,name='audit_questions'),
    path('add_moreques/',views.add_moreques,name='add_moreques'),
    path('responses/', views.responses, name='responses'),
    path('add_more/', views.add_more, name='add_more'),
    path('show_report/', views.show_report, name='show_report'),
    path('report_to_pdf/',views.PDFView,name='report_to_pdf'),
    path('pie_chart/',views.pie_chart,name='pie_chart'),
    path('save_pdf/',views.save_pdf,name='save_pdf'),
    path('upload_circulars/',views.upload_circulars,name='upload_circulars'),
    path('file_upload/',views.file_upload,name='file_upload'),
    path('delete_report/<int:report_id>/',views.delete_report,name='delete_report'),
    path('logout/', views.logout_view,name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
