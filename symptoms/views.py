from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

from symptoms.models import Symptom


@never_cache
def list_symptoms(request):
    return render(request, 'symptoms/list.html')


@never_cache
def create(request):
    if request.method == 'POST':
        symptom = Symptom()
        symptom.name = request.POST.get('symptom_name')
        symptom.description = request.POST.get('symptom_description')
        symptom.save()

        if request.POST.get('submit_and_return'):
            return redirect('symptoms:list')

        else:
            return render(request, 'symptoms/create.html', {
                'previous_symptom': symptom
            })

    else:
        return render(request, 'symptoms/create.html')

    # if request.method == 'POST' and 'submit_and_return' in request.POST:
    #     new_symptom = Symptom(name=request.session['symptom_name'],
    #                           description=request.session['symptom_description'],
    #                           is_active=False,
    #                           date_created=True,
    #                           date_updated=True)
    #     new_symptom.save()
    #
    # elif request.method == 'POST' and 'submit_and_duplicate' in request.POST:
    #     new_symptom = Symptom(name=request.session['symptom_name'],
    #                           description=request.session['symptom_description'],
    #                           is_active=False,
    #                           date_created=True,
    #                           date_updated=True)
    #     new_symptom.save()
    #     new_symptom.pk = None
    #     new_symptom.state.adding = True
    #     new_symptom.save()

    # return render(request, 'symptoms/create.html')


@never_cache
def userid(request):
    return render(request, 'symptoms/userid.html')