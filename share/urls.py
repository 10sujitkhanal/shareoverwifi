from django.urls import path
from . import views

urlpatterns = [
    path('', views.display_page, name='display_page'),
    path('update_text/', views.update_text, name='update_text'),
    path('get_content/', views.get_content, name='get_content'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'), # New
    path('clear_all_images/', views.clear_all_images, name='clear_all_images'),
]