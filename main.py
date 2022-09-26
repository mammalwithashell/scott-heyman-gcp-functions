from datetime import datetime
from email import message
from urllib import response
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import Gmail_API_Lib
import Track_API_Lib
from models import BaseResponse, GeneralChecksResponse, LateCheckinsCheckResponse
import lovely_logger as log

app = FastAPI(
    title="ScotHeymanApi",
    description="Whatever Scott Heyman wants to use as the description",
    version="1.0.0",
    docs_url="/"
    )

sched = AsyncIOScheduler()

@app.on_event("startup")
def startup():
    log.init("file.log")
    sched.start()

@app.post("/example")
def example(number_input:int) -> str:
    """
    Example POST Method
    """
    response = BaseResponse()

    try:
        # Some logic
        response.message = f"{number_input * 2}"
        response.success = True

    except Exception as e:
        response.error = str(e)
        response.success = False

    return response

@app.get("/general_checks", response_model=GeneralChecksResponse)
def general_checks():
    """
    Get messages from Gmail, Check UMC & Start New Checkins Check
    """
    response = GeneralChecksResponse()

    try:
        todays_checkins = Track_API_Lib.get_todays_arrivals_units_and_names()
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
        regular_interval_check_time = datetime.now()
        response.success = True

    except Exception as e:
        response.error = str(e)
        response.success = False
    
    return response

@app.get("/late_checkins_check", response_model=LateCheckinsCheckResponse)
def late_checkins_check():
    """
    Checking for late checkins
    Get messages from Gmail
    Get today's checkins
    Process missing checkins

    """
    response = LateCheckinsCheckResponse()

    try:

        log.info('Checking for late checkins')
        msg_info = Gmail_API_Lib.get_gmail_subjects_and_dates() #E-mail subjects and dates
        log.info('Got messages from Gmail')
        log.info('Getting todays checkins')
        todays_checkins = Track_API_Lib.get_todays_arrivals_units_and_names()
        log.info('Processing missing checkins')
        missing_checkins = Gmail_API_Lib.check_for_checkins(msg_info, todays_checkins) #Already strips non-PC properties
        log.info('Processing missing checkins')
        late_checkins_time = datetime.now() #subtract an hour to ensure the execution time doesn't keep creeping up over time.
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

    except Exception as e:
        response.error = str(e)
        response.success = False

    return response

@app.get("/clean_property_check")
def clean_property_check():
    """
    Check between 7am EST and 8pm EST and again at 3am EST
    Checks every hour. Need to keep file updated with properties that have PC locks
    """
    # if ((current_hour >= 7 and current_hour <= 21) or current_hour == 3): #Check between 7am EST and 8pm EST and again at 3am EST
    #         if ((check_for_cleans_time + datetime.timedelta(hours = 1)) <= today):  #Checks every hour. Need to keep file updated with properties that have PC locks
    #             log.info('Checking for cleaned properties')
    #             #Set cleaned property statuses in Track
    #             msg_info = Gmail_API_Lib.get_gmail_subjects_and_dates() #E-mail subjects and dates
    #             log.info('Got messages from Gmail')
    #             cleaned_units = Gmail_API_Lib.check_for_cleaners(msg_info) #Need to ensure Point Central has people properly labeled
    #             inspected_units = Gmail_API_Lib.check_for_inspectors(msg_info) #Figure out what to do with Inspected Units
    #             ready_units = Track_API_Lib.add_clean_and_inspected(cleaned_units, inspected_units)
    #             log.info("Updating clean properties")
    #             if (ready_units != None):
    #                 res = Track_API_Lib.set_unit_clean_status(ready_units, 1) #Sets units to clean. 1 sets status to clean
    #             log.info("Updating clean combo properties")
    #             res = Track_API_Lib.set_combo_properties_clean_status() #Sets combo properties to clean. Need to manually keep this list up to date. Is it necessary?
    #             log.info('Set unit statuses')
    #             check_for_cleans_time = today
    #         if (current_hour == unclean_property_alert_hour): #Check at ~3pm EST (2pm CST) and alert
    #             if ((set_cleans_time + datetime.timedelta(hours = 1)) < today):
    #                 #Alert for non-clean units
    #                 log.info('Checking for unclean properties to alert')
    #                 msg_info = Gmail_API_Lib.get_gmail_subjects_and_dates() #E-mail subjects and dates
    #                 log.info('Got messages from Gmail')
    #                 todays_checkins = Track_API_Lib.get_todays_arrivals_units_and_names()
    #                 check_for_clean = Gmail_API_Lib.remove_non_PC_properties(todays_checkins) #Removes non PC Properties from the clean check
    #                 unclean_units = Track_API_Lib.check_unclean_units(check_for_clean) #Need to cross reference the unit name as well
    #                 #Handle combo units based on what Track says
    #                 log.info('Sending Slack alerts if any')
    #                 for unit in unclean_units:
    #                     last_access = Gmail_API_Lib.last_cleaner(msg_info, unit['unit_name'])
    #                     res = Slack_API_Lib.send_slack_message('automated-alerts',"UNCLEAN CHECKIN POSSIBLE! " + last_access)
    #                 set_cleans_time = today
    pass