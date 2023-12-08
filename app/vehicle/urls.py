"""
URL mappings for the recipe app.
"""

from django.urls import path, include

from rest_framework.routers import DefaultRouter

from vehicle import views


router = DefaultRouter()
router.register('vehicles', views.VehicleViewSet)
router.register('tags', views.TagViewSet)
router.register('specifications', views.SpecificationViewSet)
app_name = 'vehicle'

urlpatterns = [
    path('', include(router.urls)),
]
