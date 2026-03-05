import asyncio
from datetime import datetime
import main
from scraper import config, utils
from scraper.roles import fetch_roles

# Set today's date as the CSV output filename
today_date = datetime.now().strftime("%m-%d-%Y")
config.CSV_OUTPUT = f"{today_date}.csv"
config.LAST_N_HOURS = 24  # Scrape today's links only

def get_custom_roles():
    """Fetch roles from API and use only the 'name' field for search terms."""
    api_roles = fetch_roles()
    custom_roles = []
    for item in api_roles:
        name = item.get("name")
        if name:
            # Using the name as both the domain name and the search term
            # as requested: "take only the value that assigned to variable 'name'"
            custom_roles.append({
                "name": name,
                "terms": [name]
            })
    return custom_roles

# Wrap the CSV writer and DB inserter to filter for US locations only
from scraper import db

original_csv_writer = main.csv_writer
original_db_insert = db.insert_job

async def filtered_csv_writer(job):
    if utils.is_us_location(job.get("location", ""), job.get("country", "")):
        await original_csv_writer(job)

async def filtered_db_insert(job):
    if utils.is_us_location(job.get("location", ""), job.get("country", "")):
        return await original_db_insert(job)
    return "filtered" # Return a status indicating it was skipped

# Monkey-patch main.csv_writer and db.insert_job
main.csv_writer = filtered_csv_writer
db.insert_job = filtered_db_insert

async def run_scraper():
    roles = get_custom_roles()
    if not roles:
        print("No roles found from API. Aborting.")
        return
    await main.run(limit=0, custom_roles=roles)

if __name__ == "__main__":
    asyncio.run(run_scraper())
