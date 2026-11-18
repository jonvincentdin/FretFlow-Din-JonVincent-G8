from django.urls import path

from . import views

app_name = 'songs'

urlpatterns = [
    path('', views.song_list, name='list'),
    path('new/', views.song_create, name='create'),
    path('<int:pk>/', views.song_detail, name='detail'),
    path('<int:pk>/edit/', views.song_edit, name='edit'),
    path('<int:pk>/delete/', views.song_delete, name='delete'),
]
