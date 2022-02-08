from django.shortcuts import render


# Create your views here.
def list(request):
    return render(request, 'symptom/list.html')


def create(request):
    return render(request, 'symptom/create.html')


def userid(request):
    return render(request, 'symptom/userid.html')

