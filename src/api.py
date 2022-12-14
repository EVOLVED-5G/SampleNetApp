import time
from flask import Flask, request, jsonify
import requests
import evolved5g
import os
import subprocess
import json
from queue import Queue
import netapp_utils
import redis
from threading import Thread

from evolved5g.sdk import LocationSubscriber ,CAPIFInvokerConnector
from evolved5g.swagger_client.rest import ApiException
from evolved5g.swagger_client import LoginApi, User ,Configuration ,ApiClient
from evolved5g.swagger_client.models import Token


def register_function():
    subprocess.run(["sh", "./prepare.sh"], stderr=subprocess.PIPE, text=True)


policy_db={}

vapp_db={
    'host_name':"",
    'port':0,
    'token':0
}

q = Queue(maxsize = 1)


# netapp_host=os.environ['netapp_host']
# netapp_ip=os.environ['netapp_ip']
# netapp_port=os.environ['netapp_port']
# netapp_callback_port=os.environ['netapp_callback_port']

# nef_ip=os.environ['nef_ip']
# nef_port=os.environ['nef_port']
# nef_user=os.environ['nef_user']
# nef_pass=os.environ['nef_pass']
# nef_proto=os.environ['nef_proto']

# capif_host=os.environ['capif_host']
# capif_port_http=os.environ['capif_port_http']
# capif_port_https=os.environ['capif_port_https']
# capif_certs_path=os.environ['capif_certs_path']

callback_url=os.environ["CALLBACK_ADDRESS"]
netapp_address=os.environ["NETAPP_ADDRESS"]
netapp_info=netapp_address.split(":")
netapp_ip=netapp_info[0]
netapp_port=netapp_info[1]

netapp_info=netapp_address.split(":")
netapp_host=netapp_info[0]
netapp_callback_port=netapp_info[1]


capif_host=os.environ['CAPIF_HOSTNAME']
capif_port_http=os.environ['CAPIF_PORT_HTTP']
capif_port_https=os.environ['CAPIF_PORT_HTTPS']
capif_certs_path=os.environ['PATH_TO_CERTS']

nef_address=os.environ['NEF_ADDRESS']
nef_user=os.environ['NEF_USER']
nef_pass=os.environ['NEF_PASSWORD']

nef_info=nef_address.split(":")
nef_ip=nef_info[0]
nef_port=nef_info[1]
nef_url="http://{}:{}".format(nef_ip,nef_port)

# capif_registration={
#   "folder_to_store_certificates": capif_certs_path,
#   "capif_host": capif_host,
#   "capif_http_port": capif_port_http,
#   "capif_https_port": capif_port_https,
#   "capif_netapp_username": "zortenet_user",
#   "capif_netapp_password": "zorte_netapp_password",
#   "capif_callback_url": "http://{}:{}".format(netapp_host,netapp_callback_port),
#   "description": "zorte_app_description",
#   "csr_common_name": "zorte_app_common_name",
#   "csr_organizational_unit": "zorte_app_ou",
#   "csr_organization": "zorte_app_o",
#   "crs_locality": "Athens",
#   "csr_state_or_province_name": "Athens",
#   "csr_country_name": "GR",
#   "csr_email_address": "zorte@example.com"
# }

# json_object = json.dumps(capif_registration, indent=4)
# with open("./capif_registration.json", "w") as outfile:
#     outfile.write(json_object)



# thread = Thread(target = register_function)
# thread.start()

#subprocess.run(["sh", "./prepare.sh"], stderr=subprocess.PIPE, text=True)

# subprocess.Popen(["sh", "./prepare.sh"])
print("------>",nef_user)
print("------>",nef_pass)
print("------>",nef_url)

token=netapp_utils.get_token(nef_user,nef_pass,nef_url)
print(token)         
#location_subscriber = LocationSubscriber(nef_url, token,  capif_certs_path, capif_host, capif_port_https)


app = Flask(__name__)



@app.route('/', methods=["GET", "POST"])
def index():
    return netapp_host,netapp_ip


@app.route('/vapp_connect',methods=["POST"])
def vappConnect():
    data=request.json
    vapp_ip=data['vapp_ip']
    port=data['port']

    vapp_db['host_name']=vapp_ip
    vapp_db['port']=port
    vapp_db['token']=token

    return vapp_db['token']


@app.route('/subscription_capif', methods=["POST"])
def vappRegister_capif():
    data = request.json
    _id=data['id']
    numOfreports=data['num_of_reports']
    exp_time=data['exp_time']


    location_subscriber = LocationSubscriber(nef_url = nef_url,
                                             nef_bearer_access_token = token,
                                             folder_path_for_certificates_and_capif_api_key=capif_certs_path,
                                             capif_host=capif_host,
                                             capif_https_port=capif_port_https)

    subscription=""
    resp="OK"
    # try:


    subscription = location_subscriber.create_subscription(
        netapp_id="zorte_netapp",
        external_id=_id,
        notification_destination="http://{}:{}/netAppCallback".format(netapp_host,netapp_callback_port),
        maximum_number_of_reports=numOfreports,
        monitor_expire_time=exp_time
    )


    monitoring_response = subscription.to_dict()
    print(monitoring_response)


    # except evolved5g.swagger_client.rest.ApiException as e:
    #     resp="ApiException"
    #     # print(e.message)




    return resp


@app.route('/subscription', methods=["POST"])
def vappRegister():
    data = request.json
    _id=data['id']
    numOfreports=data['num_of_reports']
    exp_time=data['exp_time']

    token = vapp_db['token']

    location_subscriber = LocationSubscriber(nef_url, token)


    subscription=""
    resp="OK"
    try:


        subscription = location_subscriber.create_subscription(
            netapp_id=netapp_host,
            external_id=_id,
            notification_destination="http://{}:{}/netAppCallback".format(netapp_host,netapp_port),
            maximum_number_of_reports=numOfreports,
            monitor_expire_time=exp_time
        )




    except evolved5g.swagger_client.rest.ApiException as e:
        resp="ApiException"




    return resp


@app.route('/setPolicy',methods=["POST"])
def setPolicy():
    data = request.json
    print(data)
    pid=data['pol-id']
    exid=data['id']
    cells=data['cells']
    policy_db[exid]={
        "policy_id":pid,
        "cells":cells
    }
    print(policy_db)
    return data




@app.route('/get_subscriptions',methods=["GET"])
def get_subsciptions():

    resp="OK"
    location_subscriber = LocationSubscriber(nef_url, token)
    try:
        all_subscriptions = location_subscriber.get_all_subscriptions(netapp_host, 0, 100)
        print(all_subscriptions)

    except ApiException as ex:
        resp="ApiException"


    return resp


@app.route('/VappConsume',methods=["GET","POST"])
def VappConsume():
    log_record={
        "nothing":"nothing"
    }
    if(not q.empty()):
        log_record=q.get()

    return log_record



@app.route('/netAppCallback',methods=["GET","POST"])
def netAppCallback():

    data = request.json

    d={
        'policy':policy_db,
        'msg':data
    }

    print(data)


    ex_id=data['externalId']
    if ex_id in policy_db:
        if data['locationInfo']['cellId'] not in policy_db[ex_id]['cells']:
            data['type']='alert'
        else:
            data['type']='log'
    else:
        data['type']='log'        


    payload={
        "data":data
    }
    headers = {
        'Content-type': 'application/json'
    }

    try:
        auth_response = requests.post("http://{}:{}/vapp_callback".format(vapp_db['host_name'],vapp_db['port']), headers=headers,json=payload)
    except:
        pass

    if(q.empty()):
        q.put(data)
    else:
        q.get()
        q.put(data)

    return jsonify(data)

if __name__ == '__main__':   
    app.run(host="0.0.0.0",port=5000,debug=True)


