# Generated by Django 3.2.23 on 2023-12-08 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20231208_2112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicle',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]