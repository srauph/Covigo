# Generated by Django 4.0.2 on 2022-03-01 00:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientSymptom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.TextField(blank=True, null=True)),
                ('is_hidden', models.BooleanField(default=False)),
                ('is_viewed', models.BooleanField(default=False)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Symptom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('users', models.ManyToManyField(related_name='symptoms', through='symptoms.PatientSymptom', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='patientsymptom',
            name='symptom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patient_symptoms', to='symptoms.symptom'),
        ),
        migrations.AddField(
            model_name='patientsymptom',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patient_symptoms', to=settings.AUTH_USER_MODEL),
        ),
    ]
