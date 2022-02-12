# from django.db import models
# from django.contrib.auth.models import User
#
#
# class Symptom(models.Model):
#     users = models.ManyToManyField(
#         User,
#         related_name="users",
#         through='PatientSymptom'
#     )
#     name = models.CharField(max_length=255, blank=True, null=True)
#     description = models.TextField(blank=True, null=True)
#     is_active = models.BooleanField(blank=True, null=True)
#     date_created = models.DateTimeField(blank=True, null=True)
#     date_updated = models.DateTimeField(blank=True, null=True)
#
#     def __str__(self):
#         return self.name
#
#
# class PatientSymptom(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
#     data = models.TextField(blank=True, null=True)
#     is_hidden = models.BooleanField(blank=True, null=True)
#     is_viewed = models.BooleanField(blank=True, null=True)
#     due_date = models.DateTimeField(blank=True, null=True)
#     date_created = models.DateTimeField(blank=True, null=True)
#     date_updated = models.DateTimeField(blank=True, null=True)
#
#     class Meta:
#         constraints = [
#             models.UniqueConstraint()
#         ]
#     def __str__(self):
#         return "{}_{}".format(self.user.__str__(), self.symptom.__str__())
