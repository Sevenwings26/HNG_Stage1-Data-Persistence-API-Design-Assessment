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

2. Sorting

sort_by → age | created_at | gender_probability
order  → asc | desc


Example: /api/profiles?sort_by=age&order=desc




3. Pagination

page  (default: 1)
limit (default: 10, max: 50)

Response format:
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 2026,
  "data": [ ... ]
}




4. Natural Language Query (Core Feature)

Endpoint: GET /api/profiles/search



Example: /api/profiles/search?q=young males from nigeria


Your system must interpret plain English queries and convert them into filters. Pagination (page, limit) applies here too.



Example mappings:



"young males"                          → gender=male + min_age=16 + max_age=24
"females above 30"                     → gender=female + min_age=30
"people from angola"                   → country_id=AO
"adult males from kenya"               → gender=male + age_group=adult + country_id=KE
"male and female teenagers above 17"   → age_group=teenager + min_age=17


Rules:



 Rule-based parsing only. No AI, no LLMs
 "young" maps to ages 16–24 for parsing purposes only. It is not a stored age group
 Queries that can't be interpreted return:


  { "status": "error", "message": "Unable to interpret query" }




5. Query Validation

Invalid queries must return:



{ "status": "error", "message": "Invalid query parameters" }




6. Performance

Must handle 2026 records efficiently
Pagination must be properly implemented
Avoid unnecessary full-table scans


Error Responses

All errors follow this structure:

{ "status": "error", "message": "<error message>" }

 400 Bad Request        — Missing or empty parameter
 422 Unprocessable Entity — Invalid parameter type
 404 Not Found          — Profile not found
 500/502                — Server failure


Additional Requirements

CORS header: Access-Control-Allow-Origin: *
All timestamps in UTC ISO 8601
All IDs in UUID v7
Response structure must match exactly. Grading is partially automated



**Grading Report**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:dart: Score: 85/100 (85.0%)
:white_check_mark: Passed: 7/8
:x: Failed: 1/8
:stopwatch: Execution Time: 15.10s

**Test Results:**
:white_check_mark: combined_filters: 15/15 pts
:white_check_mark: sorting: 10/10 pts
:white_check_mark: filtering_logic: 20/20 pts
:x: 
pagination: 4/15 pts
   └─ pagination envelope invalid for page=1&limit=5; page overlap detected or insufficient records; limit max-cap behavior is invalid
:white_check_mark: query_validation: 3/5 pts
:white_check_mark: performance: 5/5 pts
:white_check_mark: natural_language_parsing: 20/20 pts
:white_check_mark: readme_explanation: 8/10 pts
[4:03 AM]:tada: Passed! Score: 85/100