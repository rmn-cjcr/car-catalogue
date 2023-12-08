"""
Views for the vehicle APIs.
"""
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Vehicle, Tag, Specification
from vehicle import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='comma separated list of tag IDs to filter'
            ),
            OpenApiParameter(
                'specifications',
                OpenApiTypes.STR,
                description='comma separated list of specification IDs to filter'
            )
        ]
    )
)
class VehicleViewSet(viewsets.ModelViewSet):
    """View for manage vehicle APIs."""
    serializer_class = serializers.VehicleDetailSerializer
    queryset = Vehicle.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve vehicles for authenticated user."""
        tags = self.request.query_params.get('tags')
        specifications = self.request.query_params.get('specifications')
        queryset = self.queryset
        if tags:
            tags_ids = self._params_to_ints(tags)
            queryset = self.queryset.filter(tags__id__in=tags_ids)
        if specifications:
            specifications_ids = self._params_to_ints(specifications)
            queryset = self.queryset.filter(specifications__id__in=specifications_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.VehicleSerializer
        elif self.action == 'upload_image':
            return serializers.VehicleImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new vehicle."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload_image')
    def upload_image(self, request, pk=None):
        """Upload an image to vehicle."""
        vehicle = self.get_object()
        serializer = self.get_serializer(vehicle, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to vehicles.',
            )
        ]
    )
)
class BaseVehicleAttrClass(mixins.DestroyModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    """Base viewset for vehicle attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve vehicles for authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        query_set = self.queryset
        if assigned_only:
            query_set = query_set.filter(vehicle__isnull=False)

        return query_set.filter(user=self.request.user).order_by('-name').distinct()


class TagViewSet(BaseVehicleAttrClass):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class SpecificationViewSet(BaseVehicleAttrClass):
    """Manage specifications in the database."""
    serializer_class = serializers.SpecificationSerializer
    queryset = Specification.objects.all()
