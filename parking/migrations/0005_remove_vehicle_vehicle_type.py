# Generated by Django 5.2 on 2025-05-12 00:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0004_alter_vehicle_unique_together_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vehicle',
            name='vehicle_type',
        ),
    ]
