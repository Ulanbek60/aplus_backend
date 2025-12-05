from django.urls import path
from .views import VehicleListView, VehicleStatusHistoryView, FuelHistoryView, TrackView, EventView

urlpatterns = [
    path("list/", VehicleListView.as_view()),
    path("list/", VehicleListView.as_view()),
    path("<int:veh_id>/status/", VehicleStatusHistoryView.as_view()),
    path("<int:veh_id>/fuel/", FuelHistoryView.as_view()),
    path("<int:veh_id>/track/", TrackView.as_view()),
    path("<int:veh_id>/events/", EventView.as_view()),

]
