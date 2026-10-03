from apify_client import ApifyClientAsync
from os import getenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool


@tool('search_jobs_linkedin', description= 'Search Linkedin for job listings using parameters (location, keyword, experience_level, job_type, remote, location_radius, datePosted) based on user input. This function returns all found job listings.')
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



@tool('search_jobs_glassdoor', description= 'Search Glassdoor for job listings using parameters (location, keyword, experience_level, job_type, remote, location_radius, daysOld) based on user input. This function returns all found job listings.')
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
    model= ChatGoogleGenerativeAI(
            model= "gemini-3.8-flash",
            google_api_key = getenv("GEMINI_API_KEY")
        )

    agent= create_agent(
        model= model,
        tools= [search_jobs_on_linkedin, search_jobs_on_glassdoor]
    )

    response= await agent.ainvoke({
        'messages': [
            {'role' : 'system', 'content': 'You are a helpful assistant for finding job listings via Linkedin and Glassdoor based on user prompts.'},
            {'role' : 'user', 'content': prompt}
        ]
        })

    result= response['messages'][-1].content 
    return result[0]['text']