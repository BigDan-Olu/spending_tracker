from django.contrib import admin
from .models import Profile, DailySpending, Member

admin.site.register(Profile)
admin.site.register(DailySpending)
admin.site.register(Member)