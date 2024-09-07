from django.contrib import admin
from .models import VerificationCode, Department, Project, Event, News, EmployeeProfile

admin.site.register(VerificationCode)
admin.site.register(Department)
admin.site.register(Project)
admin.site.register(Event)
admin.site.register(News)
admin.site.register(EmployeeProfile)