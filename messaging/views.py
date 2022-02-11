from django.shortcuts import render


def index(request):
    return render(request, 'messaging/index.html')

def viewMessage(request):
    return render(request, 'messaging/view-message.html')
