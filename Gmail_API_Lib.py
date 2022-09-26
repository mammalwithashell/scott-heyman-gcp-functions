#This Gmail_API_Lib also does alot of the processing of the Point Central Emails.
# import the required libraries
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import pickle
import os.path
import base64
import email
from bs4 import BeautifulSoup
import lxml
import datetime
import csv
import Slack_API_Lib
import importlib
importlib.reload(Slack_API_Lib)
import pytz
import json

last_email_subject_read_file_cleaner = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\email subject logs\\Last_Email_Read_Cleaner.txt'
last_email_subject_read_file_inspector = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\email subject logs\\Last_Email_Read_Inspector.txt'
last_email_subject_read_file_guest = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\email subject logs\\Last_Email_Read_Guest.txt'
last_email_subject_read_file_UMC = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\email subject logs\\Last_Email_Read_UMC.txt' #universal Master Code
last_email_subject_read_file_owner = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\email subject logs\\Last_Email_Read_owner.txt' #universal Master Code
property_name_key_file = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\Property Name Keys\\Property_Name_Keys.csv'
todays_checkin_filename = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\Todays_Reservation_Logs\\'



def get_gmail_subjects_and_dates():
    # Define the SCOPES. If modifying it, delete the token.pickle file.


    # Variable creds will store the user access token.
    # If no valid token found, we will create one.
    creds = None

    # The file token.pickle contains the user access token.
    # Check if it exists

    SERVICE_ACCOUNT_FILE = 'python_email_key.json'
    creds = service_account.Credentials.from_service_account_file(
        filename=SERVICE_ACCOUNT_FILE,
        scopes=['https://mail.google.com/',
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/gmail.send'],
        subject='cozi.automations@cozivr.com'
        )

    """
    # If credentials are not available or are invalid, ask the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('python_email_key.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the access token in token.pickle file for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    """

    # Connect to the Gmail API
    service = build('gmail', 'v1', credentials=creds)

    # request a list of all the messages
    result = service.users().messages().list(userId='me', maxResults='100').execute()

    # We can also pass maxResults to get any number of emails. Like this:
    # result = service.users().messages().list(maxResults=200, userId='me').execute()
    messages = result.get('messages')

    # messages is a list of dictionaries where each dictionary contains a message id.

    # iterate through all the messages
    count = -1
    msg_info_array = []
    msg_dict = {'subject':'', 'date':''}
    for msg in messages:
        count = count + 1
        # Get the message from its id
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()

        # Use try-except to avoid any Errors
        try:
            # Get value of 'payload' from dictionary 'txt'
            payload = txt['payload']
            headers = payload['headers']
            date = int(txt['internalDate'])/1000
            date = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d')

            # Look for Subject and Sender Email in the headers
            for d in headers:
                if d['name'] == 'Subject':
                    subject = d['value']
                    break
            msg_dict['subject'] = subject
            msg_dict['date'] = date
            msg_dict_copy = msg_dict.copy()
            msg_info_array.append(msg_dict_copy)
            res = service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()
            
        except:
            continue
        #msg_info_array = sorted(msg_info_array, key = lambda msg_info_array: msg_info_array['date']) #sort by date
    return msg_info_array

def check_for_cleaners(msg_info_array):  #Check google email subjects to see if a cleaner has keyed into the property
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    last_email_subject = "Initializing Last Email Subject Line"
    #cleaner_keyword = "Cleaning Code"
    cleaner_keyword = "Clean"
    units_w_cleaner = []
    try:
        with open(last_email_subject_read_file_cleaner, 'r') as f:
            last_email_subject = f.readlines()[0]
    except:
        pass
    for i in range(len(msg_info_array)):
        if (last_email_subject in msg_info_array[i]['subject']):
            break
        if (cleaner_keyword in ''.join(msg_info_array[i]['subject'].split()).lower()):
            PC_unit_name = msg_info_array[i]['subject'].split(':')[0].strip()
            units_w_cleaner.append(get_track_property_id(PC_unit_name))
    with open(last_email_subject_read_file_cleaner, 'w') as f:
        last_email_subject = f.write(msg_info_array[0]['subject'])
    if len(units_w_cleaner) > 0:
        units_w_cleaner = list(filter(None,units_w_cleaner))
        return units_w_cleaner
    else:
        return None
    
def check_for_inspectors(msg_info_array):  #Check google email subjects to see if a cleaner has keyed into the property
    last_email_subject = "Initializing Last Email Subject Line"
    #inspector_keyword = "Inspection Code"
    inspector_keyword = "Inspect"
    inspector_keyword = ''.join(inspector_keyword.split()).lower() #remove whitespace and change to lowercase
    units_w_inspector = []
    try:
        with open(last_email_subject_read_file_inspector, 'r') as f:
            last_email_subject = f.readlines()[0]
    except:
        pass
    for i in range(len(msg_info_array)):
        if (last_email_subject in msg_info_array[i]['subject']):
            break
        if (inspector_keyword in ''.join(msg_info_array[i]['subject'].split()).lower()):
            PC_unit_name = msg_info_array[i]['subject'].split(':')[0].strip()
            units_w_inspector.append(get_track_property_id(PC_unit_name))
    with open(last_email_subject_read_file_inspector, 'w') as f:
        last_email_subject = f.write(msg_info_array[0]['subject'])
    if len(units_w_inspector) > 0:
        units_w_inspector = list(filter(None,units_w_inspector))
        return units_w_inspector
    else:
        return None
    

def get_track_property_id(PC_unit_name):
    #return the Track property name from a Point Central property name
    #key file columns should be: [Track ID, Track Name, PC Name]
    with open(property_name_key_file, 'r', newline='') as csvfile:
        info = csv.reader(csvfile, delimiter=',')
        for row in info:
            if ''.join(PC_unit_name.split()).lower() in ''.join(row[1].split()).lower():
                track_unitId = row[0]
                track_unit_name = row[1]
                track_info = {'unitId': track_unitId, 'unit_name':track_unit_name}
                return track_info #If the property is found in the key file, return the info
    Slack_API_Lib.send_slack_message('automation-errors','Property ' + str(PC_unit_name) + ' not found in key file.')
    return None  #if no property is found, return None
                
            
    
def check_universal_master_code(msg_info_array):
    #check for Universal Master Code usage
    #"UNIVERSAL MASTER CODE" is string to look for
    last_email_subject = "Initializing Last Email Subject Line"
    UMC_keyword = "UNIVERSAL MASTER CODE"
    UMC_keyword = ''.join(UMC_keyword.split()).lower() #remove whitespace and change to lowercase
    try:
        with open(last_email_subject_read_file_UMC, 'r') as f:
            last_email_subject = f.readlines()[0]
    except:
        pass
    for i in range(len(msg_info_array)):
        if (last_email_subject in msg_info_array[i]['subject']):
            break
        if (UMC_keyword in ''.join(msg_info_array[i]['subject'].split()).lower()):
            PC_unit_name = msg_info_array[i]['subject'].strip()
            Slack_API_Lib.send_universal_master_code_alert(PC_unit_name, msg_info_array[i]['subject'][-9:-1])
    with open(last_email_subject_read_file_UMC, 'w') as f:  #Save first message read to a log file so it only looks at new messages.
        writing = f.write(msg_info_array[0]['subject'])
    return True

    
def check_for_checkins(msg_info_array, todays_checkins): #See if there are guests that have not yet checked in
    if (todays_checkins == None):
        return None
    CST = pytz.timezone('US/Eastern')
    current_time = datetime.datetime.now(CST)
    current_time = current_time.strftime('%H:%M')
    today = datetime.datetime.now().strftime('%Y_%m_%d')
    todays_checkin_filename_func = todays_checkin_filename + str(today)
    todays_checkins = set_todays_checkin_file(todays_checkins)
    new_checkins = []
    update_data = False
    for j in range(len(msg_info_array)):
        for i in range(len(todays_checkins)):
            if (len(todays_checkins) == 0):
                break
            elif ''.join(todays_checkins[i]['guest_name'].split()).lower() in ''.join(msg_info_array[j]['subject'].split()).lower():
                if (todays_checkins[i]['_cozi_checked_in'] == False):
                    todays_checkins[i]['_cozi_checked_in'] = True
                    new_checkins.append(todays_checkins[i])
                    update_data = True
                    break
    if update_data:
        with open(todays_checkin_filename_func, 'w', encoding = 'utf-8') as f:
            json.dump(todays_checkins, f, ensure_ascii=False, indent = 4, sort_keys = True)
        todays_checkins = remove_non_PC_properties(todays_checkins)
    if len(todays_checkins) == 0:
        return None
    else:
        return new_checkins

def alert_checkin():
    today = datetime.datetime.now().strftime('%Y_%m_%d')
    todays_checkin_filename_func = todays_checkin_filename + str(today)
    update_data = False
    with open(todays_checkin_filename_func, 'r', encoding = 'utf-8') as read_content:
        res_json = json.load(read_content)
    send_alert = []
    for i in range(len(res_json)):
        if res_json[i]['_cozi_checked_in'] == True and res_json[i]['_cozi_alerted'] == False:
            res_json[i]['_cozi_alerted'] = True
            send_alert.append(res_json[i])
            update_data = True
    if update_data:
        with open(todays_checkin_filename_func, 'w', encoding = 'utf-8') as f:
            json.dump(res_json, f, ensure_ascii=False, indent = 4, sort_keys = True)
        send_alert = remove_non_PC_properties(send_alert)
        Slack_API_Lib.alert_new_checkins(send_alert)
        return send_alert
    else:
        return False

def report_late_checkins():
    #report back list of guests who have not checked in yet according to Point Central Lock emails. Also sends slack notifications
    today = datetime.datetime.now().strftime('%Y_%m_%d')
    todays_checkin_filename_func = todays_checkin_filename + str(today)
    with open(todays_checkin_filename_func, 'r', encoding = 'utf-8') as read_content:
        res_json = json.load(read_content)
    late_checkins = []
    for res in res_json:
        if res['_cozi_checked_in'] == False:
            late_checkins.append(res)
    
    if len(late_checkins) > 0:
        late_checkins = remove_non_PC_properties(late_checkins)
        return late_checkins
    else:
        return False
        


def set_todays_checkin_file(todays_arrivals):
    today = datetime.datetime.now().strftime('%Y_%m_%d')
    todays_checkin_filename_func = todays_checkin_filename + str(today)
    write_new = False
    try: #Check to see if the file has already been created
        with open(todays_checkin_filename_func, 'r', encoding = 'utf-8') as read_content:
            res_json = json.load(read_content)
        for i in range(len(todays_arrivals)):
            for j in range(len(res_json)):
                if todays_arrivals[i]['id'] == res_json[j]['id']:
                    break
                if ((j + 1) == len(res_json)):
                    res_json.append(todays_arrivals[i]) #these won't get touched 
                    write_new = True
        if write_new == True:
            with open(todays_checkin_filename_func, 'w', encoding = 'utf-8') as f:
                json.dump(res_json, f, ensure_ascii=False, indent = 4, sort_keys = True)
        return res_json
    except: #If not, create the file
        with open(todays_checkin_filename_func, 'w', encoding = 'utf-8') as f:
            json.dump(todays_arrivals, f, ensure_ascii=False, indent = 4, sort_keys = True)
        return todays_arrivals
            

def remove_non_PC_properties(reservations):  #This removes reservations in properties that do not have Point Central Locks from a list of reservations.
    non_pc_property_IDs = [169,
                           1,
                           133,
                           242,
                           34,
                           148,
                           164,
                           243,
                           8,
                           221,
                           239,
                           134,
                           41,
                           132,
                           88,
                           89,
                           86,
                           108,
                           85,
                           84,
                           190,
                           87,
                           214,
                           184,
                           188,
                           11,
                           183,
                           171,
                           172,
                           187,
                           13,
                           168,
                           109,
                           74,
                           245,
                           246,
                           244,
                           203,
                           201,
                           202,
                           123,
                           22,
                           209,
                           160,
                           152,
                           22
                           ] #TODO: Add properties that are not in PC here.
    reservations_in_PC = reservations
    for _ in range(len(reservations_in_PC)):
        i = 0
        while (1):
            if (i >= len(reservations_in_PC) or len(reservations_in_PC) == 0):
                break
            elif reservations_in_PC[i]['unitId'] in non_pc_property_IDs:
                del reservations_in_PC[i]
                continue
            i = i + 1
    return reservations_in_PC
        
def last_cleaner(msg_info_array, unit_name):
    unit_name_comp = ''.join(unit_name.split()).lower()
    cleaner_keyword = "CLEANER"
    cleaner_keyword = ''.join(cleaner_keyword.split()).lower() #remove whitespace and change to lowercase
    inspector_keyword = "INSPECTOR"
    inspector_keyword = ''.join(inspector_keyword.split()).lower() #remove whitespace and change to lowercase
    _last_cleaner = None
    last_person = None
    date = ""
    for i in range(len(msg_info_array)):
        if (unit_name_comp in ''.join(msg_info_array[i]['subject'].split()).lower()):
            if last_person == None:
                last_person = msg_info_array[i]['subject'].split('by')[1].strip()
                date = msg_info_array[i]['date']
            if ((cleaner_keyword in ''.join(msg_info_array[i]['subject'].split()).lower())):
                if ('CLEANER' in msg_info_array[i]['subject']):
                    _last_cleaner = msg_info_array[i]['subject'].split('CLEANER')[1].strip()
                elif ('Cleaner' in msg_info_array[i]['subject']):
                    _last_cleaner = msg_info_array[i]['subject'].split('Cleaner')[1].strip()
                else:
                    _last_cleaner = msg_info_array[i]['subject'].split('cleaner')[1].strip()
                date = msg_info_array[i]['date']
                break
            elif (inspector_keyword in ''.join(msg_info_array[i]['subject'].split()).lower()):
                if ('INSPECTOR' in msg_info_array[i]['subject']):
                    _last_cleaner = msg_info_array[i]['subject'].split('INSPECTOR')[1].strip()
                elif ('Inspector' in msg_info_array[i]['subject']):
                    _last_cleaner = msg_info_array[i]['subject'].split('Inspector')[1].strip()
                else:
                    _last_cleaner = msg_info_array[i]['subject'].split('inspector')[1].strip()
                date = msg_info_array[i]['date']
                break
    if (_last_cleaner != None):
        string = unit_name + ": Cleaner/Inspector - " + _last_cleaner + " on " + date
    elif (last_person != None):
        string =  unit_name + ": NO CLEANER/INSPECTOR. Last person was " + last_person + " on: " + date
    else:
        date = msg_info_array[-1]['date']
        string = unit_name + ": NO CLEANER/INSPECTOR. " + "Not a single person since: " + date
    return string

        
        
    