import json
import requests
from datetime import datetime
from flask import Flask
from flask import request
from flask_apscheduler import APScheduler
from random import choice

app = Flask(__name__)
scheduler = APScheduler()

baseurl   = "http://yourdomain.com" # Change to your Ngrok/local server URL
recording = "/audio/unavailable.mp3" # Change to file name of your recording

# Read users allowed to log in. Modify separate users file to add new allowed users.
f = open("users.txt", "r")
users = {}
for line in f:
  user = line.strip()
  users[user] = {"loggedin": False, "incall": False}


# Automatically log out all users at 17:00
@scheduler.task("cron", id="Log out users", hour="17")
def test():
  for user in users:
    users[user]["loggedin"] = False
  

# Gets an available user and connects the call to them. If no users are available a message will be played.
@app.route("/incomingCalls", methods=['POST', 'GET'])
def incoming_call():
  
  user = get_available_user()
  
  # Connect to available user if one was found
  if user:
      response = {"connect": user, "fail": {"play": "sound/beep"}, "whenhangup": f"{baseurl}/hangup"}
      users[user]["incall"] = True
  
  # Play recording if no user was found
  else:
    response = {
      "play": f"{baseurl}{recording}", 
    }

  return json.dumps(response)


# Get a random user that is 1. Logged in and 2. Not in a call
def get_available_user(): 
  available_users = []
  for user, status in users.items():
    if status["loggedin"] and not status["incall"]:
      available_users.append(user)

  if not available_users:
    return None

  return choice(available_users)

  
# Handle all incoming sms and execute functions depending on message
@app.route("/sms", methods=['POST', 'GET'])
def sms():
  f = request.form.get("from")
  message = request.form.get("message")
  message = message.strip()

  if not f and message:
    return ""

  if f not in users:
    return ""

  if message.lower() == "log in" or message.lower() == "login":
    users[f]["loggedin"] = True
    print(users)
    return "You are now logged in"
  
  if message.lower() == "log out" or message.lower() == "logout":
    users[f]["loggedin"] = False
    print(users)
    return "You are now logged out"
  
  return "Unknown command"
  # return f"Unknown command: {message}"


# Called when a call is hung up. Sets the user that was called's "incall" status to False 
@app.route("/hangup", methods=['POST', 'GET'])
def handle_hangup():
  actions = json.loads(request.form.get("actions"))
  user = actions[1]["connect"]
  users[user]["incall"] = False
  return ""

if __name__ == '__main__':
  scheduler.init_app(app)
  scheduler.start()
  app.run(debug=True, host='127.0.0.1', port=5501)
  
