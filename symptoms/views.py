from django.shortcuts import render


# Create your views here.
def list(request):
    return render(request, 'symptoms/list.html')


def create(request):
    return render(request, 'symptoms/create.html')


def userid(request):
    return render(request, 'symptoms/userid.html')

