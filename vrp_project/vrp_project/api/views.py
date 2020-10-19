from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import generics, status
from .models import Vehicle, Customer, Batch, Solution, Address
from .serializers import VehicleSerializer, CustomerSerializer, BatchSerializer, SolutionSerializer, AddressSerializer
from rest_framework.views import APIView
from . import solver
import urllib
import json


class VehicleList(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        serializer = VehicleSerializer(queryset, many=True)
        return Response(serializer.data)


class VehicleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


class CustomerList(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = Customer.objects.all()
        batch_name = self.request.query_params.get('batch_name', None)

        # make the providing batch name optional
        # if a batch name is not provided just return all customers
        if batch_name is not None:
            queryset = Customer.objects.filter(batch__batch_name=batch_name)
        return queryset

    def list(self, request):
        queryset = self.get_queryset()
        serializer = CustomerSerializer(queryset, many=True)
        return Response(serializer.data)


class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class BatchList(generics.ListCreateAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        serializer = BatchSerializer(queryset, many=True)
        return Response(serializer.data)


class BatchDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class AddressList(generics.ListCreateAPIView):
    queryset = Address.objects.all()
    serializer_class = BatchSerializer

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        serializer = AddressSerializer(queryset, many=True)
        return Response(serializer.data)


class AddressDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class SolverView(APIView):
    def get(self, request, batch_name, time_limit):

        # if a batch object for given name does not exists return 404
        target_batch = get_object_or_404(Batch, batch_name=batch_name)

        # start the optimization task
        solver.main.delay(batch_name, time_limit)
        message = "The task started. Please return after specified time-limit to receive the solution."
        return Response({"message": message, "Time Limit (in seconds)": time_limit}, status=status.HTTP_202_ACCEPTED)


class SolutionView(APIView):
    def get(self, request, batch_name):
        target_batch = get_object_or_404(Batch, batch_name=batch_name)

        try:
            target_solution = Solution.objects.get(batch=target_batch)
            if target_solution != None:
                serialiser = SolutionSerializer(target_solution)
                return Response(serialiser.data)
        except ObjectDoesNotExist:
            message = "The solution does not exists. Please make sure you have already requested the instance to be solved."
            return Response({"message": message})
