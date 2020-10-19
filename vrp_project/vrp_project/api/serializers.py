from .models import Vehicle, Customer, Batch, Solution, Address
from rest_framework import serializers


class VehicleSerializer(serializers.ModelSerializer):
    """ a data serializer class for vehicle objects """
    class Meta:
        model = Vehicle
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    """ a data serializer class for customer objects """

    class Meta:
        model = Customer
        fields = '__all__'
        depth = 1


class BatchSerializer(serializers.ModelSerializer):
    """ a data serializer class for batch objects """
    class Meta:
        model = Batch
        fields = ['id', 'batch_name']
        depth = 1


class SolutionSerializer(serializers.ModelSerializer):
    """ a data serializer class for solution objects """
    class Meta:
        model = Solution
        fields = '__all__'
        depth = 1


class AddressSerializer(serializers.ModelSerializer):
    """ a data serializer class for address objects """
    class Meta:
        model = Address
        fields = '__all__'
        depth = 1
