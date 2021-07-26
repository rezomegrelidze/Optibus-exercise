import json
from datetime import datetime

class OptibusService:
    def __init__(self,dataFile):
        with open(dataFile) as fp:
            data = json.load(fp)
            self.stops = data['stops']
            self.trips = data['trips']
            self.vehicles = data['vehicles']
            self.duties = data['duties']
    
    def get_duty(self,duty_id : int): 
        return list(
            filter(lambda o : o["duty_id"] == str(duty_id),self.duties))[0]

    def get_vehicle(self,vehicle_id : int):
        return list(
            filter(lambda o : o["vehicle_id"] == str(vehicle_id),self.vehicles))[0]
    
    def get_trip(self,trip_id : int):
        return list(
            filter(lambda o : o["trip_id"] == str(trip_id),self.trips))[0]
    
    def get_stop(self,stop_id):
        return list(
            filter(lambda o : o["stop_id"] == stop_id,self.stops))[0]
    
    def get_duty_ids(self):
        return list(map(lambda o : int(o["duty_id"]),self.duties))
    
        
class OptibusClient:
    def __init__(self,dataFile):
        self.service = OptibusService(dataFile)

    def get_times_for_vehicle_events(self,vehicle_events,ves_number):
        event_types_list = ["deadhead","depot_pull_in","depot_pull_out","pre_trip","attendance"]
        for event in list(vehicle_events):
                if int(event["vehicle_event_sequence"]) == ves_number :
                    vehicle_event_type = event["vehicle_event_type"]
                    if vehicle_event_type == "service_trip":
                        trip_id = event["trip_id"]
                        trip = self.service.get_trip(int(trip_id))
                        return (trip["departure_time"],trip["arrival_time"])
                    elif (vehicle_event_type in event_types_list):
                        return (event["start_time"],event["end_time"])



    def get_event_times(self,duty_events):
        return list(map(lambda s : self.get_times_for_event_sequence(s),duty_events))

    def start_end_time(self,duty_id : int):
        duty = self.service.get_duty(duty_id)
        duty_events = duty["duty_events"]
        times = self.get_event_times(duty_events)
        return { 
            "Start Time" : times[0][0], 
             "End Time" : times[-1][1] }  
    
    def get_service_trips(self,vehicle_id : int,duty_id : int):
        return list(filter(lambda o : o["vehicle_event_type"] == "service_trip"
            and o["duty_id"] == str(duty_id),
            self.service.get_vehicle(vehicle_id)["vehicle_events"]))

    def first_and_last_stops(self,duty_id: int):
        duty = self.service.get_duty(duty_id)
        duty_events = duty["duty_events"]
        vehicles_events = list(
            filter(lambda o : o["duty_event_type"] == "vehicle_event",duty_events))
        vehicle_ids = list(map(lambda o : int(o["vehicle_id"]),vehicles_events))
        listOfTrips = [self.get_service_trips(id,duty_id) for id in vehicle_ids]
    
        serviceTrips = []
        for trips in listOfTrips:
            for trip in trips:
                serviceTrips.append(self.service.get_trip(int(trip["trip_id"])))
        stops = []
        for trip in serviceTrips:
            stops.append(self.service.get_stop(trip["origin_stop_id"]))
            stops.append(self.service.get_stop(trip["destination_stop_id"]))
        return { "First Stop" : stops[0]["stop_name"],"Last Stop" : stops[-1]["stop_name"]}

    def get_times_for_event_sequence(self,event_sequence):
        duty_event_type = event_sequence["duty_event_type"]
        if duty_event_type == "sign_on" or duty_event_type == "taxi":
            return (event_sequence["start_time"],event_sequence["end_time"])
        elif duty_event_type == "vehicle_event": 
            vehicle_id = int(event_sequence["vehicle_id"])
            ves_number = event_sequence["vehicle_event_sequence"]
            vehicle = self.service.get_vehicle(vehicle_id)
            vehicle_events = vehicle["vehicle_events"]
            return self.get_times_for_vehicle_events(vehicle_events,ves_number)
    
    def holes_in_times(self,times):
        if len(times) < 2: return []
        holes = []
        for i in range(1,len(times) - 1):
            prevTime = times[i-1]
            currTime = times[i]
            if prevTime[1] != currTime[0]:
                holes.append((prevTime[1],currTime[0]))
        return holes


    def timeInMinutes(self,hole : str):
        # I implement here a method to split a string in to <day offset>:<hours>:<minute> 
        initialSplit = hole.split(".")
        dayOffset = int(initialSplit[0])
        hours = int(initialSplit[1].split(":")[0])
        minutes = int(initialSplit[1].split(":")[1])
        return (dayOffset * 24 * 60) + (hours * 60) + minutes
        

    def hole_duration_in_minutes(self,hole):
        firstTime = self.timeInMinutes(hole[0])
        secondTime = self.timeInMinutes(hole[1])
        return (secondTime - firstTime)

    def break_start_and_duration(self,duty_id):
        firstDuty = self.service.get_duty(duty_id)
        times = client.get_event_times(firstDuty["duty_events"])
        # print(times)
        # print(f'holes: {self.holes_in_times(times)}')
        # print(f'hole durations: {[self.hole_duration_in_minutes(hole) for hole in self.holes_in_times(times)]}')
        breakInfoList = []
        holes = self.holes_in_times(times)
        
        for hole in holes:
            breakStart = hole[0]
            breakDuration = self.hole_duration_in_minutes(hole)
            if breakDuration >= 15: 
                breakInfoList.append({"Break Start Time" : breakStart,"Break Duration (in mintues)" : breakDuration})
        return breakInfoList;


client = OptibusClient("data.json")


for id in client.service.get_duty_ids():
    print(f'Duty Id: {id},{client.start_end_time(id)}' + 
          f',{client.first_and_last_stops(id)}' + 
          f',{client.break_start_and_duration(id)}')


