from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('events/', views.EventListView.as_view(), name='events'),
    path('events/<int:pk>', views.EventDetailView.as_view(), name='Event-detail'),
    path('contacts/', views.ContactListView.as_view(), name='contacts'),
    path('contacts/<int:pk>', views.ContactDetailView.as_view(), name='Contact-detail'),
]

urlpatterns += [
    path('myevents/', views.EventsByUserListView.as_view(), name='my-events'),
    path('eventinstances/<uuid:pk>/register/', views.register_eventinstance, name='register-eventinstance'),
    path('eventinstances/<uuid:pk>/cancel/', views.cancel_eventinstance, name='cancel-eventinstance'),
    path('accounts/register/', views.register, name='register'),
    path('staff/unapproved-users/', views.UnapprovedUsersView.as_view(), name='unapproved-users'),
]
