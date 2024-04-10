Relational Database Schema: https://drive.google.com/file/d/1PcRSKCuXbFDdfpB90IunBriXVatrEfAx/view?usp=sharing
Entity Relationship: https://drive.google.com/file/d/15S4-Cp30zAx6cSbJuGvORABpQvmakh2B/view?usp=sharing
Youtube video: https://youtu.be/rP7uBgN46z0

Admin/staff premade accounts. You can login to any of the existing users
- Admin:      "fred@gmail.com":"password123"
- Trainer:    "alice@gmail.com":"password123"
- Member:     "emily.davis@gmail.com":"password123"

Steps to run:
1. Create a database in pgadmin
2. run allAtOnceDEBUG.sql (copy and pasting into pgadmin -> query tool)
3. Change db_params for db in app.py 
4. Run CMD in admin mode and CD to top level of folder
5. Make venv `python3 -m venv venv`
6. Activate venv `venv\Scripts\activate`
7. Pip install flask and psycopg2 `pip install Flask psycopg2-binary`
8. Run flask `flask run`
9. Head to localhost:5000
        
BONUS THINGS IMPLEMENTED:
1. Hashing of passwords
2. Flask interface with beautiful UI
3. AI Generated profile pictures from [https://thispersondoesnotexist.com/]