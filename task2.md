Stage 2 task - Improve Stage 1 task
https://airtable.com/appZPpwy4dtvVBWU4/shrMH9P1zv4TPhvns?C3OrT=recCRAOnUwTulDtq6 


Your Task

Upgrade your system into a Queryable Intelligence Engine. 

You will:

- Implement advanced filtering
- Add sorting and pagination
- Support combined filters
- Build a basic natural language query system


Enhancement:
1. Data Seeding
Seed your database with the 2026 profiles from this file (it is an array of Json): - https://drive.google.com/file/d/1Up06dcS9OfUEnDj_u6OV_xTRntupFhPH/view
Re-running the seed should not create duplicate records.

2. Advanced Filtering

Endpoint: GET /api/profiles



Supported filters:

gender
age_group
country_id
min_age
max_age
min_gender_probability
min_country_probability


Example: /api/profiles?gender=male&country_id=NG&min_age=25


Filters must be combinable. Results must strictly match all conditions.