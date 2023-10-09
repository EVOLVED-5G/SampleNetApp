import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import evolved5g
import os
import subprocess
import json
from queue import Queue
from threading import Thread
import datetime
from influxdb import InfluxDBClient
import sqlite3
from sqlite_utils import create_policyDB, get_ue_policies, update_policy , operation_status

from evolved5g.sdk import LocationSubscriber , QosAwareness,CAPIFInvokerConnector,UsageThreshold
from evolved5g.swagger_client.rest import ApiException
from evolved5g.swagger_client import LoginApi, User ,Configuration ,ApiClient
from evolved5g.swagger_client.models import Token


network_app_id = "Zortenetapp"

create_policyDB()


def read_and_delete_all_existing_qos_subscriptions(qos_awereness):
    
    

    try:
        all_subscriptions = qos_awereness.get_all_subscriptions(network_app_id)
        print(all_subscriptions)

        for subscription in all_subscriptions:
            id = subscription.link.split("/")[-1]
            print("Deleting subscription with id: " + id)
            qos_awereness.delete_subscription(network_app_id, id)
    except ApiException as ex:
        if ex.status == 404:
            print("No active transcriptions found")
        else: 
            raise




def read_and_delete_all_existing_location_subscriptions(location_subscriber):


    try:
        all_subscriptions = location_subscriber.get_all_subscriptions(network_app_id, 0, 100)

        print(all_subscriptions)

        for subscription in all_subscriptions:
            id = subscription.link.split("/")[-1]
            print("Deleting subscription with id: " + id)
            location_subscriber.delete_subscription(network_app_id, id)
    except ApiException as ex:
        if ex.status == 404:
            print("No active transcriptions found")
        else: 
            raise



q = Queue(maxsize = 1)



influx_ip=os.getenv('INFLUX_IP')
influx_port=os.getenv('INFLUX_PORT')


client = InfluxDBClient(influx_ip,influx_port, 'admin' , 'admin')
client.switch_database('influx')


nef_url = "https://{}:{}".format(os.getenv('NEF_IP'), os.environ.get('NEF_PORT'))


nef_callback_location = "http://{}:{}/netAppCallback_{}".format(os.getenv('NEF_CALLBACK_IP'), os.environ.get('NEF_CALLBACK_PORT'),"location")
nef_callback_qos = "http://{}:{}/netAppCallback_{}".format(os.getenv('NEF_CALLBACK_IP'), os.environ.get('NEF_CALLBACK_PORT'),"qos")


nef_user = os.getenv('NEF_USER')
nef_pass = os.environ.get('NEF_PASS')
capif_host = os.getenv('CAPIF_HOSTNAME')
capif_https_port = os.environ.get('CAPIF_PORT_HTTPS')
folder_path_for_certificates_and_capif_api_key = os.environ.get('PATH_TO_CERTS')



qos_awereness = QosAwareness(nef_url,folder_path_for_certificates_and_capif_api_key, capif_host, capif_https_port)
location_subscriber = LocationSubscriber(nef_url,folder_path_for_certificates_and_capif_api_key, capif_host, capif_https_port)


read_and_delete_all_existing_qos_subscriptions(qos_awereness)
read_and_delete_all_existing_location_subscriptions(location_subscriber)





app = Flask(__name__)
CORS(app)


ue_mapping_qos={
    "10.0.0.3":"camera_controler",
    "10.0.0.2":"robot_arm",
    "10.0.0.1":"industrial_belt"
}

ue_mapping_location={
    "10003@domain.com":"camera_controler",
    "10002@domain.com":"robot_arm",
    "10001@domain.com":"industrial_belt"
}


devs=[
    {
        "tags": {"device": "camera_controler"},
        "measurement": "devices",
        "fields":{"empty":"empty"}
    },
    {
        "tags": {"device": "robot_arm"},
        "measurement": "devices",
        "fields":{"empty":"empty"}
    },
    {
        "tags": {"device": "industrial_belt"},
        "measurement": "devices",
        "fields":{"empty":"empty"}
    }
]

client.write_points(devs)




@app.route('/', methods=["GET"])
def index():
    return {
            "response":{
                "data":"zorte_netapp is up"
            }
        }



@app.route('/nef_qos', methods=["GET"])
def qos_subscr():
    

    mon_eq=["10.0.0.1","10.0.0.2","10.0.0.3"]
    qos_awereness = QosAwareness(nef_url,folder_path_for_certificates_and_capif_api_key, capif_host, capif_https_port)


    for meq in mon_eq:

        
        equipment_network_identifier = meq
        network_identifier = QosAwareness.NetworkIdentifier.IP_V4_ADDRESS
        conversational_voice = QosAwareness.GBRQosReference.CONVERSATIONAL_VOICE
        # In this scenario we monitor UPLINK
        uplink = QosAwareness.QosMonitoringParameter.UPLINK
        # Minimum delay of data package during uplink, in milliseconds
        uplink_threshold = 20
        gigabyte = 1024 * 1024 * 1024
        # Up to 10 gigabytes 5 GB downlink, 5gb uplink
        usage_threshold = UsageThreshold(duration=None,  # not supported
                                         total_volume=10 * gigabyte,  # 10 Gigabytes of total volume
                                         downlink_volume=5 * gigabyte,  # 5 Gigabytes for downlink
                                         uplink_volume=5 * gigabyte  # 5 Gigabytes for uplink
                                         )


        try:

            subscription = qos_awereness.create_guaranteed_bit_rate_subscription(
                netapp_id=network_app_id,
                equipment_network_identifier=equipment_network_identifier,
                network_identifier=network_identifier,
                notification_destination=nef_callback_qos,
                gbr_qos_reference=conversational_voice,
                usage_threshold=usage_threshold,
                qos_monitoring_parameter=uplink,
                threshold=uplink_threshold,
                reporting_mode=QosAwareness.EventTriggeredReportingConfiguration(wait_time_in_seconds=1)
            )

            qos_awereness_response = subscription.to_dict()
        except:
            pass

    return {"response":"qos subscriptions created"}




@app.route('/nef_location', methods=["GET"])
def location_subscr():


    mon_eq=["10001@domain.com","10002@domain.com","10003@domain.com"]


    for meq in mon_eq:

        external_id=meq
        times=1000
        expire_time=(datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

        try:

            subscription = location_subscriber.create_subscription(
                netapp_id=network_app_id,
                external_id=external_id,
                notification_destination=nef_callback_location,
                maximum_number_of_reports=times,
                monitor_expire_time=expire_time
            )

            monitoring_response = subscription.to_dict()
        except:
            pass




    return {"response":"location subscriptions created"}





# @app.route('/set_location_policy',methods=["GET"])
# def setLocPolicy():

#     pid=1
#     exid="10003@domain.com"
#     cells="AAAAA1001,AAAAA1002"
#     policy_db[exid]={
#         "policy_id":pid,
#         "cells":cells
#     }
 
#     return {"response":"policy enforced"}


@app.route('/setPolicy',methods=["POST"])
def setPolicy():
    data = request.json

    ue = data['ue']
    update_policy("1",ue)
    in_policy = get_ue_policies()
 

    return {"in_policy":in_policy}



@app.route('/removePolicy',methods=["POST"])
def removePolicy():
    data = request.json

    ue = data['ue']
    update_policy("0",ue)
    in_policy = get_ue_policies()


    return {"in_policy":in_policy}



# @app.route('/VappConsume',methods=["GET","POST"])
# def VappConsume():
#     log_record={
#         "nothing":"nothing"
#     }
#     if(not q.empty()):
#         log_record=q.get()

#     return log_record


@app.route('/check_operation',methods=["GET"])
def check_operation():

    return operation_status(client)



@app.route('/netAppCallback_qos',methods=["GET","POST"])
def netAppCallback_qos():

    in_policy = get_ue_policies()

    data = request.json

    ipv4Addr = data["ipv4Addr"]
    event = data["eventReports"][0]['event']


    data_point={
                "tags": {"device": ue_mapping_qos[ipv4Addr]},
                "measurement": "nef_qos",
                "fields":{
                    "event":event
                    
                }
        }


    client.write_points([data_point])
    


    data_point={
        "tags": {"none": "none"},
        "measurement": "alerts",
        "fields":{
            "event": "",
            "status":""
            
        }
    }


    op_status = operation_status(client)

    if(op_status["operation"]):
        if(len(in_policy)==0):
            data_point["fields"]["event"] = "No QoS policy enforced"
        else:
            data_point["fields"]["event"] = "QoS of [{}] is quaranteed".format(','.join(in_policy))
        

        data_point["fields"]["status"] = "Running"

    else:
        data_point["fields"]["event"] = "QoS of [{}] is not quaranteed overall".format(','.join(in_policy))        
        data_point["fields"]["status"] = "Stopped"



    client.write_points([data_point])


    return jsonify(data)




# @app.route('/netAppCallback_location',methods=["GET","POST"])
# def netAppCallback_location():

#     data = request.json

#     d={
#         'policy':policy_db,
#         'msg':data
#     }

#     cell_id = data["locationInfo"]["cellId"]
#     externalId = data["externalId"]
#     ipv4Addr = data["ipv4Addr"]
#     enodeBId = data["locationInfo"]["enodeBId"]

#     data_point={
#                 "tags": {"device": ue_mapping_location[externalId]},
#                 "measurement": "nef_location_log",
#                 "fields":{
#                     "cellId":cell_id,
#                     "externalId":externalId
#                 }
#         }

#     print(data)


#     ex_id=data['externalId']
#     if ex_id in policy_db:
#         if data['locationInfo']['cellId'] not in policy_db[ex_id]['cells']:
#             data_point["measurement"] = "nef_location_alert"
#             data['type']='alert'
#         else:
#             data['type']='log'
#     else:
#         data['type']='log'        



#     client.write_points([data_point])


#     payload={
#         "data":data
#     }
#     headers = {
#         'Content-type': 'application/json'
#     }


#     if(q.empty()):
#         q.put(data)
#     else:
#         q.get()
#         q.put(data)

#     return jsonify(data)

if __name__ == '__main__':   
    app.run(host='0.0.0.0',port=5000,debug=True)


