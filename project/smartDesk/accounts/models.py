from django.db import models
from django.contrib.auth.models import User
import random

class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def generate_code(cls):
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects')
    team_members = models.ManyToManyField(User, related_name='projects')

class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateTimeField()

class News(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_published = models.DateTimeField(auto_now_add=True)

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    is_department_head = models.BooleanField(default=False)