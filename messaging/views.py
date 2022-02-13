from django.shortcuts import render


def index(request):
    return render(request, 'messaging/index.html')

def composeMessage(request):
    return render(request, 'messaging/composeMessage.html')