from apify_client import ApifyClientAsync
from os import getenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool
from .models import SearchInfo, LLMResult, JobListingResult
from asgiref.sync import sync_to_async
import traceback


async def search_jobs_on_linkedin(
        location: str, 
        keyword: str, 
        experience_level: str, 
        job_type: str, 
        remote: str, 
        location_radius: int | None= None, 
        limitPerSource: int = 10, 
        datePosted: str = 'pastMonth'
):
    api_token= getenv('APIFY_API_TOKEN')

    client= ApifyClientAsync(api_token)
    actor= client.actor("curious_coder/linkedin-jobs-scraper")
    
    keyword_parts= [keyword, experience_level, job_type, remote]
    keyword_str= " ".join(part for part in keyword_parts if part)


    run_input= {
    "keywords": keyword_str,
    "location": location,
    "limitPerSource": limitPerSource,
    "datePosted": datePosted,
    }

    if location_radius is not None:
        run_input["distance"] = location_radius

    run= await actor.call(run_input= run_input)
    dataset= client.dataset(run.default_dataset_id)

    items= await dataset.list_items()
    return items.items




async def search_jobs_on_glassdoor(
        location: str, 
        keyword: str, 
        experience_level: str, 
        job_type: str, 
        remote: str, 
        location_radius: int | None= None, 
        limit: int = 10, 
        daysOld: str = 30
):
    api_token= getenv('APIFY_API_TOKEN')

    client= ApifyClientAsync(api_token)
    actor= client.actor("valig/glassdoor-jobs-scraper")
    
    keyword_parts= [keyword, experience_level, job_type, remote]
    keyword_str= " ".join(part for part in keyword_parts if part)


    run_input= {
    "keywords": keyword_str,
    "location": location,
    "limit": limit,
    "daysOld": daysOld,
    }

    if location_radius is not None:
        run_input["distance"] = location_radius

    run= await actor.call(run_input= run_input)
    dataset= client.dataset(run.default_dataset_id)

    items= await dataset.list_items()
    return items.items



async def search_jobs_with_agent(prompt: str) -> str:
    collected_jobs= []

    #linkedin tool
    @tool('search_jobs_linkedin', description= 'Search Linkedin for job listings using parameters (location, keyword, experience_level, job_type, remote, location_radius, datePosted) based on user input. This function returns all found job listings.')
    async def linkedin_tool(
        location: str, 
        keyword: str, 
        experience_level: str, 
        job_type: str, 
        remote: str, 
        location_radius: int | None= None, 
        limitPerSource: int = 15, 
        datePosted: str = "pastMonth"
    ):
        items = await search_jobs_on_linkedin(
            location= location, keyword= keyword, experience_level= experience_level, job_type= job_type, remote= remote, location_radius= location_radius, limitPerSource= limitPerSource, datePosted= datePosted
        )

        for item in items:
            collected_jobs.append({
                "source" : "LinkedIn",
                "data": item
            })

        return items


    # glassdoor tool
    @tool('search_jobs_glassdoor', description= 'Search Glassdoor for job listings using parameters (location, keyword, experience_level, job_type, remote, location_radius, daysOld) based on user input. This function returns all found job listings.')
    async def glassdoor_tool(
        location: str, 
        keyword: str, 
        experience_level: str, 
        job_type: str, 
        remote: str, 
        location_radius: int | None= None, 
        limit: int = 30, 
        daysOld: str = 30
    ):
        items = await search_jobs_on_glassdoor(
            location= location, keyword= keyword, experience_level= experience_level, job_type= job_type, remote= remote, location_radius= location_radius, limit= limit, daysOld= daysOld
        )

        for item in items:
            collected_jobs.append({
                "source" : "Glassdoor",
                "data": item
            })

        return items


    #model running
    model= ChatGoogleGenerativeAI(
            model= "gemini-3.8-flash",
            google_api_key = getenv("GEMINI_API_KEY")
        )

    agent= create_agent(
        model= model,
        tools= [linkedin_tool, glassdoor_tool]
    )

    response= await agent.ainvoke({
        'messages': [
            {'role' : 'system', 'content': 'You are a helpful assistant for finding job listings via Linkedin and Glassdoor based on user prompts.'},
            {'role' : 'user', 'content': prompt}
        ]
        })

    result= response['messages'][-1].content 
    return result[0]['text'], collected_jobs


# converting result into db records
def normalize_job(item, source):
    return {
        "title": (
            item.get("title")
            or item.get("jobTitle")
            or "Unknown title"
        ),

        "job_url": (
            item.get("job_url")
            or item.get("link")
            or item.get("url")
            or ""
        ),

        "job_type": (
            item.get("jobType")
            or item.get("employmentType")
        ),

        "level": (
            item.get("experienceLevel")
            or item.get("seniorityLevel")
            or item.get("experience")
        ),

        "summary": (
            item.get("description")
            or item.get("companyDescription")
        ),

        "salary": (
            item.get("salary")
            or item.get("salaryRange")
            or (item.get("pay") or {}).get("max")
        ),    

        "posted" : (
            item.get("ageInDays")
            or item.get("postedAt")
            or item.get("datePosted")
        ), 

        "applicants": (
            item.get("applicants")
            or item.get("applicantsCount")
        ),

        "raw_data": item,

        "source": source
    }


# conduct background search
async def process_search(search_id):
    try:
        search= await SearchInfo.objects.aget(id= search_id)

        result, jobs = await search_jobs_with_agent(search.prompt)

        # save llm result in db
        llm_result= await LLMResult.objects.acreate(
                search= search,
                result= result
            )

        # save job listings result in db
        for job in jobs:
            data= job["data"]
            source= job["source"]

            normalized= normalize_job(data, source)

            await JobListingResult.objects.acreate(
                    llm_result= llm_result,
                    **normalized
                )

        # mark search as completed

        search.status = "COMPLETED"
        await search.asave()


    except Exception as e:
        #marking search as failed

        search= await SearchInfo.objects.aget(id= search_id)

        search.status= "FAILED"
        await search.asave()

        raise

