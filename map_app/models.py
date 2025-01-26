from django.db import models

class Coordinate(models.Model):
    nama = models.CharField(max_length=255)
    kategori = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.nama
