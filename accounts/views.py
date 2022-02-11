from django.shortcuts import render

from accounts.models import Staff


def userlist(request):
    staff = justGetAStaffForNowIdcAbtAnythingElse(1)
    return render(request, 'accounts/list.html', {'staff': staff})


def justGetAStaffForNowIdcAbtAnythingElse( user_id):
    staff = Staff.objects.get(pk=user_id)
    return staff
