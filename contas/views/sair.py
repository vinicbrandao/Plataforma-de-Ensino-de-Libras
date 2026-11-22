from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View


class SairView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        return redirect("contas:entrar")
