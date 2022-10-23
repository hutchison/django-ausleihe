from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

class Home(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'ausleihe/home.html')
