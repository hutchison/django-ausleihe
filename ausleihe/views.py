from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView, ListView

from .models import (
    Buch,
    Autor,
)


class Home(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'ausleihe/home.html')


class BuchList(LoginRequiredMixin, ListView):
    queryset = Buch.objects.select_related('medium')
