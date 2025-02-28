from django.urls import path
from . import views
from . import model_run
from . import DeepThinking

urlpatterns = [
    path('', views.index, name='index'),
    path('send_message/', model_run.process_message, name='send_message'),
    path('send_message_web_search/', DeepThinking.process_message_web_search, name='send_message_web_search'),
    path('meteor_preview/', views.meteor_preview, name='meteor_preview'),
    # path('upload_file/', views.upload_file, name='upload_file'),
]
