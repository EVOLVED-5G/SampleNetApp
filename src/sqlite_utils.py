import sqlite3



map_policies={
	"camera_controler":1,
	"industrial_belt":2,
	"robot_arm":3
}



def create_policyDB():


	conn = sqlite3.connect('policies.db')

	try:
		conn.execute('''CREATE TABLE POLICIES
			 (ID INT PRIMARY KEY     NOT NULL,
			 UE           TEXT    NOT NULL,
			 QUARANTEED            INT     NOT NULL);''')



		conn.execute("INSERT INTO POLICIES (ID,UE,QUARANTEED) VALUES (1, 'camera_controler',0)");
		conn.execute("INSERT INTO POLICIES (ID,UE,QUARANTEED) VALUES (2, 'industial_belt',0)");
		conn.execute("INSERT INTO POLICIES (ID,UE,QUARANTEED) VALUES (3, 'robot_arm',0)");

		conn.commit()

	except sqlite3.OperationalError:
		pass


	conn.close()


def get_ue_policies():

	conn = sqlite3.connect('policies.db')

	cursor = conn.execute("SELECT UE FROM POLICIES WHERE QUARANTEED = 1")

	in_policy=[]

	for row in cursor:
		in_policy.append(row[0])


	conn.close()

	return in_policy



def update_policy(val,ue):

	conn = sqlite3.connect('policies.db')

	map_policies={
		"camera_controler":1,
		"industrial_belt":2,
		"robot_arm":3
	}

	conn.execute("UPDATE POLICIES set QUARANTEED = {} where ID = {}".format(val,map_policies[ue]))
	conn.commit()


	conn.close()



def operation_status(client):


    alert=False

    resp={"operation":1}

    in_policy = get_ue_policies()


    details={}


    for ue in in_policy:
        details[ue]={
            "status":"none"
        }


    try:

        query_camera ="SELECT event FROM nef_qos WHERE (device=\'camera_controler\') ORDER BY desc LIMIT 1"
        result_camera = list(client.query(query_camera))[0][0]['event']

        if('camera_controler' in details):
            details['camera_controler']["status"]=result_camera


        if('camera_controler' in in_policy and result_camera=='QOS_NOT_GUARANTEED'):
            alert=True

    except IndexError:
        pass


    try:

        query_arm ="SELECT event FROM nef_qos WHERE (device=\'robot_arm\') ORDER BY desc LIMIT 1"
        result_arm = list(client.query(query_arm))[0][0]['event']
 
        if('robot_arm' in details):
            details['robot_arm']["status"]=result_arm


        if('robot_arm' in in_policy and result_arm=='QOS_NOT_GUARANTEED'):
            alert=True
    except IndexError:
        pass


    try:

        query_belt ="SELECT event FROM nef_qos WHERE (device=\'industrial_belt\') ORDER BY desc LIMIT 1"
        result_belt = list(client.query(query_belt))[0][0]['event']


        if('industrial_belt' in details):
            details['industrial_belt']["status"]=result_arm



        if('industrial_belt' in in_policy and result_belt=='QOS_NOT_GUARANTEED'):
            alert=True


    except IndexError:
        pass



    if(alert):
        resp['operation']=0


    resp["details"]=details

    return resp