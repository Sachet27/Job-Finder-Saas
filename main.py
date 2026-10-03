from dotenv import load_dotenv
from apify_client import ApifyClient
from os import getenv

load_dotenv('job-saas/.env')
api_token= getenv('APIFY_API_TOKEN')

client= ApifyClient(api_token)

run_input= {
    "keywords": "Python Django",
    "location": "Remote",
    "limitPerSource": 3,
    "datePosted": "pastWeek"
}

run= client.actor("curious_coder/linkedin-jobs-scraper").call(run_input= run_input)

print(f"💾 Check your data here: https://console.apify.com/storage/datasets/{run.default_dataset_id}")
for item in client.dataset(run.default_dataset_id).iterate_items():
    print(item)