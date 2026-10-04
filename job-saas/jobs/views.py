from django.shortcuts import render, redirect
from .tasks import run_search
from .models import LLMResult, JobListingResult, SearchInfo
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


# Create your views here.
@login_required(redirect_field_name= 'login')
async def search_job_view(request):
    
    if request.method == 'POST':
        prompt= request.POST.get('prompt')
        
        search= await SearchInfo.objects.acreate(
            title= "New Job Search",
            prompt= prompt,
            status= "RUNNING",
            owner= request.user
        )

        run_search.delay(search.id)

        return render(request, 'jobs/search.html', {'search_id' : search.id})

    return render(request, 'jobs/search.html')


@login_required
async def search_status_view(request, search_id):
    try:
        search = await SearchInfo.objects.aget(id= search_id, owner = request.user)
        
        if search.status == "RUNNING":
            return JsonResponse({'status': "RUNNING"})

        if search.status == "FAILED":
            return JsonResponse({'status': "FAILED"})

        #display results
        if search.status == "COMPLETED":
            return JsonResponse({
                "status" : "COMPLETED",
                "redirect_url" : f"/search/{search.id}/results/"
            })
        

    except SearchInfo.DoesNotExist:
        # search has failed
        return JsonResponse({'error' : 'Search record does not exist'}, status=404)
    


@login_required
async def search_results_view(request, search_id):
    try:
        search= await SearchInfo.objects.aget(id= search_id, owner= request.user)
        
        if search.status == "RUNNING":
            return redirect('search')

        if search.status == "FAILED":
            return render(request, 'jobs/results.html', {'error' : 'Failed to conduct search'})

        # completed search
        llm_result = await LLMResult.objects.aget(search = search)

        jobs= [job async for job in llm_result.job_listing_results.all()]

        context= {
            'search' : search,
            'result' : llm_result.result,
            'jobs': jobs
        }
        return render(request, 'jobs/results.html', context)

    except SearchInfo.DoesNotExist:
        return render(request, 'jobs/results.html', {'error': 'Search record does not exist'})
         