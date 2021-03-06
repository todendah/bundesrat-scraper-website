# Unofficial Bundesrat Scraper - Website

This is the UI for the [Bundesrat Scraper](https://github.com/okfde/bundesrat-scraper) data. You can check the behavior of the counties of Germany in the `Bundesrat` for a given session and `Tagesordnungspunkt`(TOP).  You can find a live demo [on Heroku](https://bundesrat-scraper-website.herokuapp.com/).

The website and scraper, including the data, scraper and website code, are unofficial. The `Bundesrat` has nothing to do with it. There is no warranty that the scraped data is correct or complete or the website displays the correct information.

You can search either for some keyword in all Tagesordnungspunkt(TOP) titles.

## Initialize


If you start the webpage for the very first time, it can take up to 30-60 seconds before you see the page. In this time, the data JSONs from the [Bundesrat Scraper](https://github.com/okfde/bundesrat-scraper) get downloaded. After this, it should be much faster.

### Setup

The setup is optimized for Arch Linux, but should work with other Linux Distros as well. Please check that you are connected to the internet.


```
yay -S heroku-cli #Or use the package manager of your distro
python3 -m venv getting-started #Derived from template of Django on Heroku
pip install -r requirements.txt
python manage.py collectstatic
python manage.py migrate
python manage.py makemigrations
python manage.py migrate 
heroku local
```

, if you want to run the website only locally. If you want to run the app on Heroku, also do:

```
heroku create #Creates new app on Herkou
git push heroku main #Push code onto heroku

heroku run python manage.py migrate #Create DB
heroku open #Go to website
```

### Drop Database if JSONs were updated

The website currently fetches the JSON data from the [Bundesrat Scraper](https://github.com/okfde/bundesrat-scraper) only when it is started the very first time. If the data was updated, do the following steps to drop the website's database and force a re-fetch of the data:

#### Drop DB Locally

```
cd bundesrat-scraper-website
rm db.sqlite3
python3 manage.py migrate
heroku local
```
and visit the local website once to start fetching.

#### Drop DB on Heroku

```
cd bundesrat-scraper-website
heroku pg:reset --confirm APPNAME
heroku run python manage.py migrate
```
and visit the website once to start fetching.

##### See remaining dyno/free hours Heroku 

```
heroku ps -a bundesrat-scraper-website #replace bundesrat-scraper-website with your app name. App name irrelevant as long as it belongs to you.
```

### Running the Test Suite

Please check that you are connected to the internet. Afterward, execute:

```
pip install coverage
coverage run --source='.' manage.py test scraper 
coverage report #To see the test coverage of files
```
