# online-grocery-store-v2
This is an enhanced version of the original Grocery Store project by me. Although it looks similar, it has various features, like mailing the user daily reminders and monthly reports. Also, there's caching for efficiency, downloading sales reports asynchronously, store manager role, etc. 

# Steps to run the project
1. cd into the "Code" folder
2. run "python app.py"
3. cd into the "frontend" folder
4. run "npm install". This might take a couple of seconds.
5. run "npm run serve"
6. Open on browser "localhost:8080"
7. register on the page and login can be done
8. All the user-end features can be used once logged in

To access the admin-end:
1. Go to login
2. Go to "manager login"
3. username: admin    password: password
4. Once logged in, all the manager-end features can be used

# Enable Mailing
1. Ensure a Redis server is running on localhost:6379
2. Ensure you have a mailing server setup, preferably Mailhog. To set up properly authenticated mailing (like Gmail), you need to make changes to the file "mail_service.py" under the "applications" folder.
3. cd into the "Code" folder
4. run "celery -A app:celery_app worker --loglevel INFO -P solo --concurrency 1" for celery worker
5. run "celery -A app.celery_app beat --max-interval 1 -l info" for celery beat
