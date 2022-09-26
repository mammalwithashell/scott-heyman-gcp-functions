import Gmail_API_Lib
import Track_API_Lib
import Slack_API_Lib
import importlib
import json
import csv
import lovely_logger as log
import datetime
import time

late_checkin_alert_hour = 21
unclean_property_alert_hour = 14
regular_check_interval_minutes = 15
check_checkin_interval_minutes = 15
reload = 1#dummy variable to make the library re-save

#All times are in local time (EST)
late_checkins_time = datetime.datetime.now() - datetime.timedelta(days = 1) #Init
alert_checkins_time = datetime.datetime.now() - datetime.timedelta(days = 1) #Init
check_for_cleans_time = datetime.datetime.now() - datetime.timedelta(days = 1) #Init
set_cleans_time = datetime.datetime.now() - datetime.timedelta(days = 1) #Init
regular_interval_check_time = datetime.datetime.now() - datetime.timedelta(days = 1) #Init
check_checkin_time = datetime.datetime.now() - datetime.timedelta(days = 1) #Init
last_email_subject_read_file_cleaner = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\email subject logs\\Last_Email_Read_Cleaner.txt'
last_email_subject_read_file_UMC = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\email subject logs\\Last_Email_Read_UMC.txt' #universal Master Code
log.init('C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\Daily_Checks_Log')

try:
    while (1):
        today = datetime.datetime.now()
        current_hour = today.hour
        
        if (check_checkin_time + datetime.timedelta(minutes = check_checkin_interval_minutes) < today): #Updates todays reservations every 15 minutes.
            log.info("Updating todays checkins")
            todays_checkins = Track_API_Lib.get_todays_arrivals_units_and_names()
            check_checkin_time = today
        
        #General checks at regular intervals
        if (regular_interval_check_time + datetime.timedelta(minutes = regular_check_interval_minutes)) < today: #Check every hour for Universal Master Code
            log.info('Getting messages from Gmail')
            msg_info = Gmail_API_Lib.get_gmail_subjects_and_dates() #E-mail subjects and dates
            log.info('Got messages from Gmail')
            #Alert for Master Code usage
            log.info('Starting UMC Check')
            UMC_check = Gmail_API_Lib.check_universal_master_code(msg_info) #Checks to see if the universal master code. Sends a Slack notification if so.
            log.info('Completed UMC Check')
            log.info('Starting New Checkins check')
            new_checkins = Gmail_API_Lib.check_for_checkins(msg_info, todays_checkins) #Already strips non-PC properties and notifies CS team in Slack
            if (len(new_checkins) > 0):
                new_alerts = Gmail_API_Lib.alert_checkin()
                Track_API_Lib.note_checkins(new_checkins)
            regular_interval_check_time = today
            

        if (current_hour == 13 or current_hour == late_checkin_alert_hour): #check for late checkins at 12pm and 8pm CST (Check twice to ensure there aren't more than 500 messages in inbox)
            if ((late_checkins_time + datetime.timedelta(hours = 1)) <= today):
                log.info('Checking for late checkins')
                msg_info = Gmail_API_Lib.get_gmail_subjects_and_dates() #E-mail subjects and dates
                log.info('Got messages from Gmail')
                log.info('Getting todays checkins')
                todays_checkins = Track_API_Lib.get_todays_arrivals_units_and_names()
                log.info('Processing missing checkins')
                missing_checkins = Gmail_API_Lib.check_for_checkins(msg_info, todays_checkins) #Already strips non-PC properties
                log.info('Processing missing checkins')
                late_checkins_time = today #subtract an hour to ensure the execution time doesn't keep creeping up over time.
                if (current_hour == late_checkin_alert_hour and missing_checkins != None): #Alert for late checkins at 8pm CST. MUST BE SAME HOUR AS IF STATEMENT ABOVE OR THIS WONT TRIGGER
                    if ((alert_checkins_time + datetime.timedelta(hours = 1)) <= today):
                        log.info('Alerting for late checkins')
                        late_checkins = Gmail_API_Lib.report_late_checkins()
                        log.info('Sending Slack notifications')
                        Slack_API_Lib.send_guest_late_checkin_alert(late_checkins)
                        log.info('Posting notes to reservations in Track')
                        Track_API_Lib.note_late_checkins(late_checkins)
                        alert_checkins_time = today
                        log.info('Completed late checkins')

        if ((current_hour >= 7 and current_hour <= 21) or current_hour == 3): #Check between 7am EST and 8pm EST and again at 3am EST
            if ((check_for_cleans_time + datetime.timedelta(hours = 1)) <= today):  #Checks every hour. Need to keep file updated with properties that have PC locks
                log.info('Checking for cleaned properties')
                #Set cleaned property statuses in Track
                msg_info = Gmail_API_Lib.get_gmail_subjects_and_dates() #E-mail subjects and dates
                log.info('Got messages from Gmail')
                cleaned_units = Gmail_API_Lib.check_for_cleaners(msg_info) #Need to ensure Point Central has people properly labeled
                inspected_units = Gmail_API_Lib.check_for_inspectors(msg_info) #Figure out what to do with Inspected Units
                ready_units = Track_API_Lib.add_clean_and_inspected(cleaned_units, inspected_units)
                log.info("Updating clean properties")
                if (ready_units != None):
                    res = Track_API_Lib.set_unit_clean_status(ready_units, 1) #Sets units to clean. 1 sets status to clean
                log.info("Updating clean combo properties")
                res = Track_API_Lib.set_combo_properties_clean_status() #Sets combo properties to clean. Need to manually keep this list up to date. Is it necessary?
                log.info('Set unit statuses')
                check_for_cleans_time = today
            if (current_hour == unclean_property_alert_hour): #Check at ~3pm EST (2pm CST) and alert
                if ((set_cleans_time + datetime.timedelta(hours = 1)) < today):
                    #Alert for non-clean units
                    log.info('Checking for unclean properties to alert')
                    msg_info = Gmail_API_Lib.get_gmail_subjects_and_dates() #E-mail subjects and dates
                    log.info('Got messages from Gmail')
                    todays_checkins = Track_API_Lib.get_todays_arrivals_units_and_names()
                    check_for_clean = Gmail_API_Lib.remove_non_PC_properties(todays_checkins) #Removes non PC Properties from the clean check
                    unclean_units = Track_API_Lib.check_unclean_units(check_for_clean) #Need to cross reference the unit name as well
                    #Handle combo units based on what Track says
                    log.info('Sending Slack alerts if any')
                    for unit in unclean_units:
                        last_access = Gmail_API_Lib.last_cleaner(msg_info, unit['unit_name'])
                        res = Slack_API_Lib.send_slack_message('automated-alerts',"UNCLEAN CHECKIN POSSIBLE! " + last_access)
                    set_cleans_time = today
        time.sleep(60)
        
except Exception as e:
    Slack_API_Lib.send_slack_message("automation-errors", "Error with the Daily Checks code. Need to restart")
    print(e)
  



#Check Track for unit clean status, and set to Clean if a claner has been there. (For combo's, both units must be Clean, then Combo can be Clean)
#Check email subjects for owners, then verify it is used during an owner stay. If not...? How about if the unit is blocked? Still notify?