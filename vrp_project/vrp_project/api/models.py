from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Vehicle(models.Model):
    """ a class representing a vehicle """
    registration_number = models.CharField(
        max_length=8, verbose_name="Registration Number", unique=True)
    color = models.CharField(max_length=255)
    make = models.CharField(max_length=255)
    capacity = models.FloatField()
    availability = models.BooleanField(default=True)

    def __str__(self):
        return (self.registration_number+" / "+str(self.capacity))


class Address(models.Model):
    """ a class representing a standard format UK address """
    TYPES_CHOICES = (
        ('HOME', 'HOME'),
        ('BUSINESS', 'BUSINESS'),
        ('OTHER', 'OTHER'),
    )
    address_type = models.CharField(max_length=20, choices=TYPES_CHOICES)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    county = models.CharField(max_length=255, blank=True)
    zip_postcode = models.CharField(max_length=8, verbose_name="Postal Code")

    def __str__(self):
        return self.zip_postcode


class Batch(models.Model):
    batch_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.batch_name


class Customer(models.Model):
    """ a class representing a delivery Customer """

    address = models.OneToOneField(
        Address, related_name='destination', on_delete=models.CASCADE)
    customer_demand = models.FloatField()
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)

    def __str__(self):
        return (self.address.zip_postcode+" / "+str(self.customer_demand))


class Solution(models.Model):
    """ a class representing a solution for a CVRP instance """
    routes = models.TextField(null=True)
    total_distance = models.FloatField()
    total_load = models.FloatField()
    solver_status = models.IntegerField(null=True)
    batch = models.OneToOneField(Batch, on_delete=models.CASCADE)

    def __str__(self):
        return self.batch.batch_name
