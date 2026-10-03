from django.shortcuts import render
from .services import search_jobs_with_agent

# Create your views here.
async def search_job_view(request):
    if request.method == 'POST':
        prompt= request.POST.get('prompt')
        result= await search_jobs_with_agent(prompt)
        return render(request, 'jobs/results.html', {'result' : result})

    return render(request)