import requests
import json
import datetime
import os
import time
import Gmail_API_Lib
import importlib
importlib.reload(Gmail_API_Lib)
import csv

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Basic ZjkzOTAxOGJiNjQzOTk5NDNlOTg2Mjg4MDhlMjBkNGU6ZTI4NWI4YjRhMmIyNjBmMDMzNTFmOTdiMzk3NDZjNDE="
}
combo_dirty_properties_list = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\Dirty Properties\\Dirty Properties.json'
combo_property_name_key_file = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\Property Name Keys\\Combo_Property_Keys.csv'
reload = 1 #dummy variable to make the library re-save

def get_availability(unitID, start_date, end_date):
    url = "https://cozivr.trackhs.com/api/v2/pms/units/" + str(unitID) + '/availability'
    end_day = datetime.datetime.strftime(end_date, '%Y-%m-%d')
    start_day = datetime.datetime.strftime(start_date, '%Y-%m-%d')
    params = {'endDate': end_day, 'startDate': start_day}
    res = requests.get(url, headers=headers, params = params)
    return url, res.json()

def get_unit_names_and_IDs(params = {'sortColumn': 'id', 'sortDirection':'asc', 'size': '100'}):
    url = "https://cozivr.trackhs.com/api/pms/units"
    units = []
    params['page']= 1 #page numbers start at 1
    res = requests.get(url, headers=headers, params = params)
    res = res.json()
    for i in range(len(res['_embedded']['units'])):
        units.append({'unitId': res['_embedded']['units'][i]['id']})
        units[-1]['unit_name'] = res['_embedded']['units'][i]['name']
    
    if(res['page_count'] > 1):
        for j in range(2,res['page_count']+1):
            params['page'] = j #page numbers start at 1
            res = requests.get(url, headers=headers, params = params)
            res = res.json()
            for i in range(len(res['_embedded']['units'])):
                units.append({'unitId': res['_embedded']['units'][i]['id']})
                units[-1]['unit_name'] = res['_embedded']['units'][i]['name']
    return units

def get_todays_arrivals(params = {'sortColumn': 'name', 'sortDirection':'asc', 'scroll': 1, 'size': 100, 'page': 1}):
    url = "https://cozivr.trackhs.com/api/pms/reservations"
    today = datetime.datetime.now()
    today = datetime.datetime.strftime(today, '%Y-%m-%d')
    params['arrivalStart'] = today
    params['arrivalEnd'] = today
    base_price_filename = 'C:\\Users\\Bailey\\Documents\\Cozi\\Automations\\Track Automations\\Reservation Logs\\' + str(today) + '.json'
    file_exists = os.path.exists(base_price_filename)
    send_track_request = True
    update_interval = 5 #minutes
    if (file_exists):
        current_time = int(time.time())
        file_update_time = os.path.getmtime(base_price_filename)
        delta = (current_time - file_update_time)/60 #convert delta time to minutes
        if delta < update_interval: #Get updated reservation data from Track if reservation data is more than an 15 minutes. Otherwise read from file.
            send_track_request = False
            try:
                with open(base_price_filename, 'r', encoding = 'utf-8') as read_content:
                    res_json = json.load(read_content)
            except:
                send_track_request = True
    if (send_track_request):
        res = requests.get(url, headers=headers, params = params)
        res_json = res.json()
        if(res_json['page_count'] > 1):
            for j in range(2,res_json['page_count']+1):
                params['page'] = j #page numbers start at 1
                res = requests.get(url, headers=headers, params = params)
                res_json = res_json + res.json()
        with open(base_price_filename, 'w', encoding = 'utf-8') as f:
            json.dump(res_json, f, ensure_ascii=False, indent = 4, sort_keys = True)
    return res_json

def get_todays_arrivals_units_and_names():
    reservations = get_todays_arrivals()
    todays_arrivals = []
    for i in range(len(reservations['_embedded']['reservations'])):
        if (reservations['_embedded']['reservations'][i]['status'] == 'Cancelled'): #Skip cancellations
            continue
        unitID = reservations['_embedded']['reservations'][i]['unitId']
        guest_name = reservations['_embedded']['reservations'][i]['_embedded']['contact']['name']   #should change this to lower case with no spaces. Also make same change to Gmail API when comparing email subject to reservation check in.
        unit_name = reservations['_embedded']['reservations'][i]['_embedded']['unit']['name']
        res_id = reservations['_embedded']['reservations'][i]['id']
        arrival_date = reservations['_embedded']['reservations'][i]['arrivalDate']
        departure_date = reservations['_embedded']['reservations'][i]['departureDate']
        type_id = reservations['_embedded']['reservations'][i]['typeId']
        booking_date_and_time = reservations['_embedded']['reservations'][i]['bookedAt']
        _cozi_checked_in = False #This is a custom variable meant to indicate whether the guest has checked in
        _cozi_alerted = False #This is a custom variable meant to inidcate whether the CS team has been alerted of this guest's checkin
        
        unit_and_res = {'unit_name': unit_name, 'unitId': unitID, 'guest_name': guest_name, 'id': res_id, 'arrivalDate': arrival_date, 'departureDate': departure_date, 'typeId': type_id, 'bookedAt': booking_date_and_time, '_cozi_checked_in': _cozi_checked_in, '_cozi_alerted': _cozi_alerted}
        todays_arrivals.append(unit_and_res)
    return todays_arrivals    
        
        
def strip_inactive_units(units):
    offboarded_keywords = ['Offboarded', 'ZZ Top Gladheart Game Room', 'Snoozed', '1103 N Llano', 'Deactivated']
    onboarding_keywords = ['Onboarding']
    offboarded_unit_list = []
    onboarding_unit_list = []
    active_unit_list = []
    
    for count in range(len(units)):
        offboarded = 0
        onboarding = 0
        for keyword in offboarded_keywords:
            if (keyword in units[count]['unit_name']):
                offboarded = 1
                break
        for keyword in onboarding_keywords:
            if (keyword in units[count]['unit_name']):
                onboarding = 1
                break
        if (offboarded == 1):
            offboarded_unit_list.append(units[count])
        elif (onboarding == 1):
            onboarding_unit_list.append(units[count])
        else:
            active_unit_list.append(units[count])
            
    return active_unit_list, offboarded_unit_list, onboarding_unit_list

def get_units_blocked_days_in_date_range(start_date, end_date, units, params = {'sortColumn': 'id', 'sortDirection':'asc', 'size': '100'}):
    start_day = datetime.datetime.strftime(start_date, '%Y-%m-%d')
    end_day = datetime.datetime.strftime(end_date, '%Y-%m-%d')
    params['startDateEnd'] = end_day
    params['endDateStart'] = start_day
    params['page'] = 1
    url = "https://cozivr.trackhs.com/api/pms/unit-blocks"
    res = requests.get(url, headers=headers, params = params)
    res = res.json()
    blocks = []
    if (len(res['_embedded']['unitBlocks']) > 0):
        for count in range(len(res['_embedded']['unitBlocks'])):
            blocks.append(res['_embedded']['unitBlocks'][count])
        for j in range(2,res['page_count']+1):
            params['page'] = j
            res = requests.get(url, headers=headers, params = params)
            res = res.json()
            for count in range(len(res['_embedded']['unitBlocks'])):
                blocks.append(res['_embedded']['unitBlocks'][count])
    for count in range(len(units)):
        for i in range(len(blocks)):
            if blocks[i]['unitId'] == units[count]['unitId']:
                units = count_blocked_days(units, count, start_date, end_date, blocks[i]['startDate'], blocks[i]['endDate'])
    return units
            
            
def count_blocked_days(units, count, start_date, end_date, block_start, block_end): #get start and end of blocked days. Clip the window if block starts or ends outside start_day and end_day.
    block_start = datetime.datetime.strptime(block_start, '%Y-%m-%d')
    block_end = datetime.datetime.strptime(block_end, '%Y-%m-%d')
    if start_date <= block_start: #_date is used for a datetime object. _day is used for a date sring in the form "2022-06-30"
        min_date = block_start
    else:
        min_date = start_date
    if end_date >= block_end:
        max_date = block_end
    else:
        max_date = end_date
    
    num_days = max_date - min_date
    num_days = num_days.days
    for day in range(num_days):
        date = min_date + datetime.timedelta(days=day)
        date = datetime.datetime.strftime(date, '%Y-%m-%d')
        units[count][date] = 'blocked'
    return units
        
def get_unit_clean_status(unit_ID):
    url = "https://cozivr.trackhs.com/api/pms/units/" + str(unit_ID) + "/clean-status"
    response = requests.get(url, headers=headers)
    res = response.json()
    try:
        return res['name']
    except:
        raise ValueError(res)
    
def check_unclean_units(todays_arrival_units):
    unclean_units = []
    for i in range(len(todays_arrival_units)):
        if not (unit_clean_check(todays_arrival_units[i]['unitId'])):
            unclean_units.append(todays_arrival_units[i])
    return unclean_units

def _FIRST_ATTEMPT_check_unclean_units(todays_arrival_units):
    set_properties_for_clean_check(todays_arrival_units)
    with open(dirty_properties_list, 'r', encoding = 'utf-8') as read_content:
        res_json = json.load(read_content)
    i = 0
    while (1):
        if (i >= len(res_json)):
            break
        clean_status = unit_clean_check(res_json[i]['unitId'])
        if (clean_status):
            del res_json[i]
        else:
            i = i + 1
    if (len(res_json) > 0):
        with open(dirty_properties_list, 'w', encoding = 'utf-8') as f:
            json.dump(todays_arrival_units, f, ensure_ascii=False, indent = 4, sort_keys = True)
    else:
        with open(dirty_properties_list, 'w', encoding = 'utf-8') as f:
            json.dump("", f, ensure_ascii=False, indent = 4, sort_keys = True)
    return

def combo_set_properties_for_clean_check(todays_arrival_units):
    todays_arrival_units = Gmail_API_Lib.remove_non_PC_properties(todays_arrival_units) #Remove units that do not have PC locks.
    file_exists = os.path.exists(dirty_properties_list)
    with open(dirty_properties_list, 'w', encoding = 'utf-8') as f:
        json.dump(todays_arrival_units, f, ensure_ascii=False, indent = 4, sort_keys = True)
    return
    

def unit_clean_check(unit_ID):
    status = get_unit_clean_status(unit_ID)
    if "Clean" in status:
        return True
    else:
        return False

    
def set_unit_clean_status(units, reason):
    #source can be phone, status, assignment, grid, checkin, checkout, or cancellation
    #reason 1: Clean
    #reason 2: Occupied
    #reason 3: Inspection
    #reason 4: Dirty
    #reason 5: In-Progress
    if (isinstance(units,int)): #Overloaded function. If units is passed as a single interger ID, use this.
        url = "https://cozivr.trackhs.com/api/pms/units/" + str(units) + "/clean-status"
        payload = {
        "id": reason,
        "source": "status"
        }
        res = requests.put(url, json=payload, headers=headers) #Set the clean status
    else:
        for i in range(len(units)):
            url = "https://cozivr.trackhs.com/api/pms/units/" + units[i]['unitId'] + "/clean-status"
            payload = {
            "id": reason,
            "source": "status"
            }
            res = requests.put(url, json=payload, headers=headers) #Set the clean status
    return res

def set_combo_properties_clean_status():
    with open(combo_property_name_key_file, 'r', newline='') as csvfile:
        info = csv.reader(csvfile, delimiter=',')
        next(info)
        for row in info:
            if row[0] == None:
                continue
            if (unit_clean_check(row[1]) == "Clean"): #Check the combo property to see if it already says clean
                continue
            for i in range(2,len(row)): #Check child properties. If they are all clean, set combo property to clean. starts at the first child property column (column C if opened in excel)
                if (unit_clean_check(row[i]) != "Clean"):
                    break
                elif (i == len(row) - 1):
                    res = set_unit_clean_status(row[1], 1)
    return

def add_clean_and_inspected(cleaned_units, inspected_units):
    if (cleaned_units == None and inspected_units == None):
        return None
    elif (cleaned_units != None and inspected_units == None):
        return cleaned_units
    elif (cleaned_units == None and inspected_units != None):
        return inspected_units
    else:
        return cleaned_units + inspected_units

def note_checkins(reservations):
    if (reservations == None or len(reservations) == 0):
        return None
    note = "Guest has now checked in"
    for reservation in reservations:
        res = add_note_to_reservation(reservation, note)
    return res

def note_late_checkins(reservations):
    if (reservations == None or len(reservations) == 0):
        return None
    note = "CS notified guest has still not checked in"
    for reservation in reservations:
        res = add_note_to_reservation(reservation, note)
    return res

def add_note_to_reservation(reservation, note):
    reservation_number = reservation['id']
    url = "https://cozivr.trackhs.com/api/pms/reservations/" + str(reservation_number) + "/notes"
    payload = {
        "note": note,
        "isPublic": False
    }
    res = requests.post(url, json=payload, headers=headers)
    return res

def get_cleaning_workorders(start_date, end_date):
    url = "https://cozivr.trackhs.com/api/pms/housekeeping/work-orders"
    params = {
        "sortColumn": 'id',
        "sortDirection":'asc',
        "startDate":start_date,
        "endDate":end_date,
        "page":1
        }
    work_orders = []
    res = requests.get(url, headers=headers, params = params)
    res_json = res.json()
    work_orders = res_json['_embedded']['workOrders']
    if(res_json['page_count'] > 1):
        for j in range(2,res_json['page_count']+1):
            params['page'] = j #page numbers start at 1
            res = requests.get(url, headers=headers, params = params)
            res_json = res.json()
            work_orders.extend(res_json['_embedded']['workOrders'])
    return work_orders

def get_units_w_hottubs_and_pools(): #Update this to include pools as well
    url = "https://cozivr.trackhs.com/api/pms/units"
    params = {
        'sortColumn':'name',
        'sortDirection':'asc',
        'amenityId':'185',  #Hottub Amenity ID
        }

    res = requests.get(url, headers=headers, params = params)
    res_json = res.json()
    units = res_json['_embedded']['units']
    if(res_json['page_count'] > 1):
        for j in range(2,res_json['page_count']+1):
            params['page'] = j #page numbers start at 1
            res = requests.get(url, headers=headers, params = params)
            res_json = res.json()
            units.extend(res_json['_embedded']['units'])
    valid_units = []
    for unit in units:
        if unit['isActive']:
            valid_units.append(unit)
    return valid_units
    
    
    
