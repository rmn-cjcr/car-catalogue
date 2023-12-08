"""Test for vehicle APIs."""
from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Vehicle, Tag, Specification

from vehicle.serializers import VehicleSerializer, VehicleDetailSerializer


VEHICLES_URL = reverse('vehicle:vehicle-list')


def detail_url(vehicle_id):
    """Create and return a vehicle detail URL."""
    return reverse('vehicle:vehicle-detail', args=[vehicle_id])


def image_upload_url(vehicle_id):
    """Create and return an image upload URL."""
    return reverse('vehicle:vehicle-upload-image', args=[vehicle_id])


def create_vehicle(user, **params):
    """Create and return a sample vehicle."""
    defaults = {
        'make': 'Sample make',
        'model': 'Sample model',
        'price': Decimal(5.25),
        'description': 'Sample description',
        'link': 'http://example.com/vehicle.pdf'
    }
    defaults.update(params)

    vehicle = Vehicle.objects.create(user=user, **defaults)
    return vehicle


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicVehicleAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(VEHICLES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateVehicleAPITests(TestCase):
    """Test authenticated API requests."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass123')
        self.client.force_authenticate(self.user)

    def test_retrieve_vehicle(self):
        """Test retrieving a list of vehicles."""
        create_vehicle(user=self.user)
        create_vehicle(user=self.user)

        res = self.client.get(VEHICLES_URL)

        vehicles = Vehicle.objects.all().order_by('-id')
        serializer = VehicleSerializer(vehicles, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_limited_to_user(self):
        """Test list of vehicles is limited to authenticated user."""
        other_user = create_user(email='other@example.com', password='password123')
        create_vehicle(user=other_user)
        create_vehicle(user=self.user)

        res = self.client.get(VEHICLES_URL)

        vehicles = Vehicle.objects.filter(user=self.user)
        serializer = VehicleSerializer(vehicles, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_vehicle_detail(self):
        """Test get vehicle detail."""
        vehicle = create_vehicle(user=self.user)

        url = detail_url(vehicle.id)
        res = self.client.get(url)

        serializer = VehicleDetailSerializer(vehicle)
        self.assertEqual(res.data, serializer.data)

    def test_create_vehicle(self):
        """Test creating a vehicle."""
        payload = {
            'model': 'New model',
            'make': 'New Make',
            'price': Decimal('5.99'),
            'description': 'New vehicle description',
        }
        res = self.client.post(VEHICLES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        vehicle = Vehicle.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(vehicle, k), v)
        self.assertEqual(vehicle.user, self.user)

    def test_partial_update(self):
        """Test partial update of vehicle."""
        original_link = 'https://example.xom/vehicle.pdf'
        vehicle = create_vehicle(
            user=self.user,
            model='Sample vehicle model',
            make='Sample vehicle make',
            link=original_link,
        )

        payload = {'model': 'New vehicle model'}
        url = detail_url(vehicle.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.model, payload.get('model'))
        self.assertEqual(vehicle.link, original_link)
        self.assertEqual(vehicle.user, self.user)

    def test_full_update(self):
        """Test full update of a vehicle."""
        vehicle = create_vehicle(
            user=self.user,
        )

        payload = {
            'model': 'New model',
            'make': 'New Make',
            'link': 'https://example.xom/new_vehicle.pdf',
            'description': 'New vehicle description',
            'price': Decimal('2.50')
        }
        url = detail_url(vehicle.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        vehicle.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(vehicle, k), v)
        self.assertEqual(vehicle.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the vehicle user results in an error."""
        new_user = create_user(email='user2@example.com', password='testpass123')
        vehicle = create_vehicle(
            user=self.user,
        )

        payload = {
            'user': new_user.id
        }
        url = detail_url(vehicle.id)
        self.client.patch(url, payload)

        vehicle.refresh_from_db()
        self.assertEqual(vehicle.user, self.user)

    def test_delete_vehicle(self):
        """Test deleting a vehicle successful."""
        vehicle = create_vehicle(user=self.user)

        url = detail_url(vehicle.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vehicle.objects.filter(id=vehicle.id).exists())

    def test_delete_other_users_vehicle_error(self):
        """Test trying to delete another users vehicle gives error."""
        new_user = create_user(email='user2@example.com', password='testpass123')
        vehicle = create_vehicle(user=new_user)

        url = detail_url(vehicle.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Vehicle.objects.filter(id=vehicle.id).exists())

    def test_create_vehicle_with_new_tags(self):
        """Test creating a vehicle with new tags."""
        payload = {
            'model': 'First model',
            'make': 'First Make',
            'price': Decimal('2.50'),
            'tags': [{'name': 'Fast'}, {'name': 'Slow'}]
        }

        res = self.client.post(VEHICLES_URL, data=payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        vehicles = Vehicle.objects.filter(user=self.user)
        self.assertEqual(vehicles.count(), 1)
        vehicle = vehicles[0]
        self.assertEqual(vehicle.tags.count(), 2)
        for tag in payload['tags']:
            exists = vehicle.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_vehicle_with_existing_tags(self):
        """Test creating a vehicle with existing tag."""
        tag_fast = Tag.objects.create(user=self.user, name='Fast')
        payload = {
            'model': 'First model',
            'make': 'First Make',
            'price': Decimal('4.50'),
            'tags': [{'name': 'Fast'}, {'name': 'Slow'}]
        }

        res = self.client.post(VEHICLES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        vehicles = Vehicle.objects.filter(user=self.user)
        self.assertEqual(vehicles.count(), 1)
        vehicle = vehicles[0]
        self.assertEqual(vehicle.tags.count(), 2)
        self.assertIn(tag_fast, vehicle.tags.all())
        for tag in payload['tags']:
            exists = vehicle.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating vehicle."""
        vehicle = create_vehicle(self.user)

        payload = {'tags': [{'name': 'Fast'}]}
        url = detail_url(vehicle.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Fast')
        self.assertIn(new_tag, vehicle.tags.all())

    def test_update_vehicle_assign_tag(self):
        """Test assigning an existing tag when updating a vehicle."""
        tag_fast = Tag.objects.create(user=self.user, name='Fast')
        vehicle = create_vehicle(user=self.user)
        vehicle.tags.add(tag_fast)

        tag_slow = Tag.objects.create(user=self.user, name='Slow')
        payload = {'tags': [{'name': 'Slow'}]}
        url = detail_url(vehicle.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_slow, vehicle.tags.all())
        self.assertNotIn(tag_fast, vehicle.tags.all())

    def test_clear_vehicle_tags(self):
        """Test clearing a vehicles tags."""
        tag = Tag.objects.create(user=self.user, name='Fast')
        vehicle = create_vehicle(self.user)
        vehicle.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(vehicle.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(vehicle.tags.count(), 0)

    def test_create_vehicle_with_new_specifications(self):
        """Test creating a vehicle with new specifications."""
        payload = {
            'model': 'First model',
            'make': 'First make',
            'price': Decimal('2.50'),
            'specifications': [{'name': '4x4'}, {'name': 'turbo'}]
        }

        res = self.client.post(VEHICLES_URL, data=payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        vehicles = Vehicle.objects.filter(user=self.user)
        self.assertEqual(vehicles.count(), 1)
        vehicle = vehicles[0]
        self.assertEqual(vehicle.specifications.count(), 2)
        for specification in payload['specifications']:
            exists = vehicle.specifications.filter(name=specification['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_vehicle_with_existing_specifications(self):
        """Test creating a vehicle with existing specifications."""
        specification_all_wheel = Specification.objects.create(user=self.user, name='4x4')
        payload = {
            'model': 'First model',
            'make': 'First make',
            'price': Decimal('4.50'),
            'specifications': [{'name': '4x4'}, {'name': 'turbo'}]
        }

        res = self.client.post(VEHICLES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        vehicles = Vehicle.objects.filter(user=self.user)
        self.assertEqual(vehicles.count(), 1)
        vehicle = vehicles[0]
        self.assertEqual(vehicle.specifications.count(), 2)
        self.assertIn(specification_all_wheel, vehicle.specifications.all())
        for specification in payload['specifications']:
            exists = vehicle.specifications.filter(name=specification['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_specification_on_update(self):
        """Test creating specification when updating vehicle."""
        vehicle = create_vehicle(self.user)

        payload = {'specifications': [{'name': '4x4'}]}
        url = detail_url(vehicle.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_specification = Specification.objects.get(user=self.user, name='4x4')
        self.assertIn(new_specification, vehicle.specifications.all())

    def test_update_vehicle_assign_specification(self):
        """Test assigning an existing specification when updating a vehicle."""
        specification_front_wheel = Specification.objects.create(user=self.user, name='2x4')
        vehicle = create_vehicle(user=self.user)
        vehicle.specifications.add(specification_front_wheel)

        specification_all_wheel = Specification.objects.create(user=self.user, name='4x4')
        payload = {'specifications': [{'name': '4x4'}]}
        url = detail_url(vehicle.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(specification_all_wheel, vehicle.specifications.all())
        self.assertNotIn(specification_front_wheel, vehicle.specifications.all())

    def test_clear_vehicle_specifications(self):
        """Test clearing a vehicles specifications."""
        specification = Specification.objects.create(user=self.user, name='4x4')
        vehicle = create_vehicle(self.user)
        vehicle.specifications.add(specification)

        payload = {'specifications': []}
        url = detail_url(vehicle.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(vehicle.specifications.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering vehicles by tags."""
        r1 = create_vehicle(user=self.user, model="First model", make="First make")
        r2 = create_vehicle(user=self.user, model="Second model", make="Second make")
        tag1 = Tag.objects.create(user=self.user, name='Slow')
        tag2 = Tag.objects.create(user=self.user, name='Fast')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_vehicle(user=self.user, model="Third model", make="Third make")

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(VEHICLES_URL, params)

        s1 = VehicleSerializer(r1)
        s2 = VehicleSerializer(r2)
        s3 = VehicleSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_specifications(self):
        """Test filtering vehicles by specifications."""
        r1 = create_vehicle(user=self.user, model="First model", make="First make")
        r2 = create_vehicle(user=self.user, model="Second model", make="Second make")
        sp1 = Specification.objects.create(user=self.user, name='4x4')
        sp2 = Specification.objects.create(user=self.user, name='2x2')
        r1.specifications.add(sp1)
        r2.specifications.add(sp2)
        r3 = create_vehicle(user=self.user, model="Third model", make="Third make")

        params = {'specifications': f'{sp1.id},{sp2.id}'}
        res = self.client.get(VEHICLES_URL, params)

        s1 = VehicleSerializer(r1)
        s2 = VehicleSerializer(r2)
        s3 = VehicleSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass123')
        self.client.force_authenticate(self.user)
        self.vehicle = create_vehicle(self.user)

    def tearDown(self):
        self.vehicle.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a vehicle."""
        url = image_upload_url(self.vehicle.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.vehicle.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.vehicle.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.vehicle.id)
        payload = {'image': 'not_and_image'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
