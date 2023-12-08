"""Serializers for vehicle APIs."""
from rest_framework import serializers
from core.models import Vehicle, Tag, Specification


class SpecificationSerializer(serializers.ModelSerializer):
    """Serializer for specifications."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for vehicles."""
    tags = TagSerializer(many=True, required=False)
    specifications = SpecificationSerializer(many=True, required=False)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'make', 'model', 'price', 'link', 'tags', 'specifications'
        ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, vehicle):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tags_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            vehicle.tags.add(tags_obj)

    def _get_or_create_specifications(self, specifications, vehicle):
        """Handle getting or creating specifications as needed."""
        auth_user = self.context['request'].user
        for specification in specifications:
            specification_obj, created = Specification.objects.get_or_create(
                user=auth_user,
                **specification,
            )
            vehicle.specifications.add(specification_obj)

    def create(self, validated_data):
        """Create a vehicle."""
        tags = validated_data.pop('tags', [])
        specifications = validated_data.pop('specifications', [])
        vehicle = Vehicle.objects.create(**validated_data)
        self._get_or_create_tags(tags, vehicle)
        self._get_or_create_specifications(specifications, vehicle)

        return vehicle

    def update(self, instance, validated_data):
        """Update vehicle."""
        tags = validated_data.pop('tags', None)
        specifications = validated_data.pop('specifications', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if specifications is not None:
            instance.specifications.clear()
            self._get_or_create_specifications(specifications, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class VehicleDetailSerializer(VehicleSerializer):
    """Serializer for vehicle detail view.."""

    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + ['description', 'image']


class VehicleImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to vehicles."""

    class Meta(VehicleSerializer.Meta):
        model = Vehicle
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
