# General Electric Bot

This project won 2nd prize at [this](https://www.hackerearth.com/challenges/hackathon/gea-hackathon18-1/) Hackathon.

### Chatbot

This project features a Telegram Chatbot, that first, takes the user's personal info (Phone, Email and Name) and saves it to the database.

From there on, the user can book an appointment, by providing basic info (Address, Serial No., Pin Code, Maps location, Reason for appointment & time slot).

Furthermore, the user can list, cancel and reschedule their previous appointments.

### Admin Panel

Apart from the Bot, the project also boasts a fully featured Admin panel, and CMS (content management system).

Using the Admin panel, one can easily add new Appliances, Pin codes, time slots etc. 

*The bot remains in-sync with the admin panel.*

You can also monitor the users of your bot, and perform basic CRUD operations.

Appointments can be cancelled, accepted or resolved using the Admin panel. 

### Architecture

The backend is pure-python. 

It uses [Django](https://www.djangoproject.com/) for the ORM and admin panel,
and the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for interacting with the Telegram Bot APIs.

I am using [docker service](https://docs.docker.com/engine/reference/commandline/service/) for orchestration and security.

It also uses [shiv](https://github.com/linkedin/shiv) for shipping pre-built python zipapp to the server,
eliminating the need to build dependencies on the server.
  
The Django backend uses gunicorn as a production-grade WSGI server.

The demo code has a sample SQLite database that contains the exported sample data, and some Pin Codes I entered myself.
(The project also has a simple cli for importing appliances from csv)

In production, I'm running a PostgreSQL database.

### Future work

The project does, however, have a lot of room for improvement. 
Here are some things I would like to add to it in the future:

- Error logging / Bug tracking using sentry/
- Supporting multiple chatbot platforms (The Django server makes adding new bots easier).
- Connection to General Electric APIs, so that there is no need to enter appliances, Pin codes, time slots etc. manually in the admin panel. (The server should fetch automatically)

## Local testing

### Requirements

- Linux
- Python >= 3.6 

### Install

```
$ git clone https://github.com/devxpy/gea-telegram-bot.git
$ cd gea-telegram-bot
$ virtualenv .venv
$ source .venv/bin/activate
$ ./scripts/pip-install.sh
$ ./manage.py migrate
```

### Run

```
python3 manage.py runtelebot  # runs the telgram bot server.

python3 manage.py runserver  # runs the django server (Admin Panel).

python3 manage.py import_appliances  # import appliances from a csv file.
```

## Thanks

This project would't have been possible without: 

- The wonderful people over at Telegram, who provided the telegram Bot APIs.
- The Django team, without which the Admin Panel wouldn't have been possible.
