# Generated by Django 3.1.3 on 2021-03-07 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20210222_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, help_text='Выбрать файл', null=True, upload_to='posts/', verbose_name='Изображение'),
        ),
    ]
