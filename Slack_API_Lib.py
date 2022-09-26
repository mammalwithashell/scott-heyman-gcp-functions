import os
from slack_sdk.errors import SlackApiError
import slack
from pathlib import Path
from dotenv import load_dotenv
import time

#Setup for Slack auto messaging
# path = "C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\bp-scraper-devliverable\\python\\SLACK_TOKEN.env"
load_dotenv()
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
reload = 1 #dummy variable to make the library re-save

def send_cleaning_alert(unit_name):
    alert = str(unit_name) + " has a check-in today, but is still dirty"
    channel_name = "automated-alerts"
    res = send_slack_message(channel_name, alert)
    return res

def send_universal_master_code_alert(unit_name, time_of_use):
    alert = "<@U026W6EC327> <@U02EBNH7EUD> The Universal Master Code was used: " + unit_name
    #channel_name = "umc-auto-notification"
    channel_name = "automated-alerts"
    res = send_slack_message(channel_name, alert)
    return res

def send_guest_late_checkin_alert(late_guest_list):
    for i in range(len(late_guest_list)):
        alert = late_guest_list[i]['guest_name'] + ' has not yet checked into the property.'
        #channel_name = "automated-checkin-notifications"
        channel_name = "automated-alerts"
        res = send_slack_message(channel_name, alert)
    return res

def alert_new_checkins(new_checkins):
    if (len(new_checkins) == 0):
        return None
    else:
        for i in range(len(new_checkins)):
            if new_checkins[i]['typeId'] == 2:
                alert = "OWNER: " + new_checkins[i]['guest_name'] + ' has arrived.'
            else:
                alert = "GUEST: " + new_checkins[i]['guest_name'] + ' has arrived.'
            #channel_name = "automated-checkin-notifications"
            channel_name = "automated-alerts"
            res = send_slack_message(channel_name, alert)
        return res

def send_slack_message(channel_name, message):
    res = client.chat_postMessage(channel=channel_name, text=message)
    time.sleep(5)
    return res
