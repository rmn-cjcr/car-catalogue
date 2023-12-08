"""Tests for the specifications API."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Specification, Vehicle

from vehicle.serializers import SpecificationSerializer

SPECIFICATIONS_URL = reverse('vehicle:specification-list')


def detail_url(specification_id):
    """Create and return a specification detail url."""
    return reverse('vehicle:specification-detail', args=[specification_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicSpecificationsApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving specifications."""
        res = self.client.get(SPECIFICATIONS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateSpecificationsAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_specifications(self):
        """Test retrieving a list of specifications."""

        Specification.objects.create(user=self.user, name="4x4")
        Specification.objects.create(user=self.user, name="2x4")

        res = self.client.get(SPECIFICATIONS_URL)
        specifications = Specification.objects.all().order_by('-name')
        serializer = SpecificationSerializer(specifications, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_limited_to_user(self):
        """Test list of specifications is limited to authenticated user."""
        other_user = create_user(email='other@example.com')
        Specification.objects.create(user=other_user, name="4x4")
        specification = Specification.objects.create(user=self.user, name='2x4')

        res = self.client.get(SPECIFICATIONS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0].get('name'), specification.name)
        self.assertEqual(res.data[0].get('id'), specification.id)

    def test_update_specification(self):
        """Test updating a specification."""
        specification = Specification.objects.create(user=self.user, name="4x4")

        payload = {'name': '2x4'}
        url = detail_url(specification.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        specification.refresh_from_db()
        self.assertEqual(specification.name, payload.get('name'))

    def test_delete_specifications(self):
        """Test deleting a specifications."""
        specification = Specification.objects.create(user=self.user, name="4x4")

        url = detail_url(specification.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        specifications = Specification.objects.filter(user=self.user)
        self.assertFalse(specifications.exists())

    def test_filter_specifications_assigned_to_vehicles(self):
        """Test listing specifications by those assigned to vehicles"""
        spec1 = Specification.objects.create(user=self.user, name='4x4')
        spec22 = Specification.objects.create(user=self.user, name='2x4')
        vehicle = Vehicle.objects.create(
            model='First model',
            make='First make',
            price=Decimal('4.50'),
            user=self.user
        )
        vehicle.specifications.add(spec1)

        res = self.client.get(SPECIFICATIONS_URL, {'assigned_only': 1})

        s1 = SpecificationSerializer(spec1)
        s2 = SpecificationSerializer(spec22)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_specifications_unique(self):
        """Test filtered specifications returns a unique list."""
        spec = Specification.objects.create(user=self.user, name='4x4')
        Specification.objects.create(user=self.user, name='2x4')
        vehicle1 = Vehicle.objects.create(
            model='First model',
            make='First make',
            price=Decimal('4.50'),
            user=self.user
        )
        vehicle2 = Vehicle.objects.create(
            model='Second model',
            make='Second make',
            price=Decimal('5.50'),
            user=self.user
        )
        vehicle1.specifications.add(spec)
        vehicle2.specifications.add(spec)

        res = self.client.get(SPECIFICATIONS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
