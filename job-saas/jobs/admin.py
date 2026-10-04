from django.contrib import admin
from .models import JobListingResult, LLMResult, SearchInfo

# Register your models here.
admin.site.register(SearchInfo)
admin.site.register(JobListingResult)
admin.site.register(LLMResult)