# -*-coding:utf-8 -*-
from django.shortcuts import render

def battle(request):
    return render(request, 'tankonline.html')
