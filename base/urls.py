from django.urls import path
from . import views

urlpatterns = [
    path('', views.lobby),
    path('room/', views.room,name='room'),
    path('get_token/', views.getToken),
    path('get_rtm_token/', views.get_rtm_token),

    path('create_member/', views.createMember),
    path('get_member/', views.getMember),
    path('delete_member/', views.deleteMember),
    path('animation/',views.animation_view,name='animation'),
  
   
]