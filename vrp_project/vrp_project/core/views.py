from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.views import View
from django.http import HttpResponse


class TestView(APIView):

    def get(self, request):
        return Response('this is a test')

    def post(self, request):
        pass
