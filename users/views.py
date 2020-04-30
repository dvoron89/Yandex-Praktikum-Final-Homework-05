from django.shortcuts import render
from django.views.generic import CreateView

from django.urls import reverse_lazy

from .forms import CreationForm

from django.shortcuts import redirect

class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'