# Generated by Django 4.2.10 on 2025-04-24 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='status',
            field=models.CharField(choices=[('LOST', 'LOST'), ('FOUND', 'FOUND'), ('CLAIMED', 'CLAIMED'), ('RETURNED', 'RETURNED')], default='LOST', max_length=20),
        ),
    ]
