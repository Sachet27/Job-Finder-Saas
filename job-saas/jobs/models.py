from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class SearchInfo(models.Model):
    STATUS_CHOICES = [
        ("RUNNING", 'Running'),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    title= models.CharField(max_length=256)
    prompt= models.TextField()
    status= models.CharField(max_length=64, choices= STATUS_CHOICES, default='RUNNING')

    owner= models.ForeignKey(User, on_delete= models.CASCADE, related_name='llm_results')

class LLMResult(models.Model):
    search = models.OneToOneField(
        SearchInfo,
        on_delete= models.CASCADE,
        related_name= 'llm_result'
    )

    result= models.TextField()
    created_at = models.DateTimeField(auto_now_add= True)




class JobListingResult(models.Model):
    title = models.CharField(max_length=1024)
    job_url = models.URLField(max_length=1024)
    job_type = models.CharField(max_length=1024, null= True, blank= True)
    level = models.CharField(max_length=1024, null= True, blank= True)
    summary = models.CharField(max_length=1024, null= True, blank= True)
    salary = models.CharField(max_length=1024, null= True, blank= True)
    posted = models.CharField(max_length=1024, null= True, blank= True)
    applicants = models.IntegerField(null=True, blank= True)
    raw_data= models.JSONField(default= dict, blank= True)
    source = models.CharField(max_length=64, null= True)

    llm_result = models.ForeignKey(LLMResult, on_delete= models.CASCADE, related_name= 'job_listing_results')


