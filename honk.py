import requests
import json
import sys
import uuid
import base64
import random

def usage():
	print("""Ring bolt scooters from python
Author: Cabbache

Usage: python3 honk.py [command] [args]

commands:
	gentoken [phone number with international prefix]  | Generate authentication token (by sms)
	show [authenticated token]  | Show available scooters in the area
	honk [authenticated token] [scooter id]  | Honk scooter

examples:
	python3 honk.py gentoken 35612312342
	python3 honk.py show KzEyMzEyMzpkamRvMjNpamQzMm9mCg==
	python3 honk.py honk KzEyMzEyMzpkamRvMjNpamQzMm9mCg== 229229
	""")

def randSequence(ranges, length):
	total = list()
	for r in ranges:
		total.extend(list(range(ord(r[0]), ord(r[1])+1)))
	return "".join([chr(random.choice(total)) for x in range(length)])

#Most API require at least these parameters
def get_params():
	return "deviceId="+randSequence([['0', '9'], ['a', 'z'], ['A', 'Z']], 22)+"&device_name=unknownAndroid%20SDK%20built%20for%20x86&device_os_version=11&deviceType=android&country=mt&language=en&version=CA.5.78"

def exitOnError(JSONresponse):
	if JSONresponse is None:
		print("Response is empty")
	elif JSONresponse["code"]:
		print("Server returned an error, see the response:")
		print(json.dumps(JSONresponse, indent=2, sort_keys=True))
	else:
		return
	sys.exit(0)

def getHeaders(token=None, jsonC=False):
	headers = {
		'User-Agent': 'okhttp/3.12.6'
	}
	if token:
		headers["Authorization"] = "Basic " + token
	if jsonC:
		headers["Content-Type"] = "application/json; charset=UTF-8"
	return headers

#type check for scooter may not be necesarry
def filterScooters(vehicleJSON):
	return [scoot for scoot in vehicleJSON["data"]["categories"][0]["vehicles"] if scoot["type"] == "scooter"]

def reqVehicles(token):
	#The API requires parameters lat and lng, random coordinates are hardcoded here
	params = "&".join([
		"lat=35.900667786675236",
		"lng=14.483184003641218",
		get_params()
	])
	response = requests.get(
		"https://rental-search.bolt.eu/categoriesOverview?"+params,
		headers=getHeaders(token)
	)
	return json.loads(response.text)

def reqHonk(token, scooter):
	params = get_params() #if the user coordinates are not supplied, the API ignores distance
	data={"vehicle_id": scooter["id"]}
	response = requests.post("https://global-rental.taxify.eu/client/ringVehicle?"+params, headers=getHeaders(token), data=data)
	return json.loads(response.text)
	
def reqPhone(phone):
	data = {
		"phone": "+"+phone,
		"phone_uuid": str(uuid.uuid4()),
		"preferred_verification_method": "sms",
		"android_hash_string": "WdpiXhIekmh",
		"appsflyer_id": randSequence([['0', '9']], 13) + "-" + randSequence([['0', '9']], 19)
	}
	response = requests.post(
		"https://user.bolt.eu/user/register/phone?",
		data=data,
		headers=getHeaders()
	)
	return json.loads(response.text), data["phone_uuid"]

def reqVerify(vcode, phone, uuid_):
	data = {
		"phone": "+"+phone,
		"phone_uuid": uuid_,
		"verification": {
			"confirmation_data": {
				"code": vcode
			},
			"method": "sms"
		}
	}
	params = get_params()
	response = requests.post(
		"https://user.bolt.eu/user/v1/confirmVerification?"+params,
		data=json.dumps(data),
		headers=getHeaders(jsonC=True)
	)
	return json.loads(response.text)

if len(sys.argv) <= 2:
	usage()
	sys.exit(0)

if sys.argv[1] == "gentoken":
	phone = sys.argv[2].replace("+", "")
	print("Requesting authentication for +"+phone)
	response, phone_uuid = reqPhone(phone)
	exitOnError(response)
	token = base64.b64encode(("+"+phone+":"+phone_uuid).encode()).decode("ascii")
	print("Your token "+token+" will be activated after verifying sms code")
	verification = input("Enter SMS verification code >> ")
	response = reqVerify(verification, phone, phone_uuid)
	exitOnError(response)
	print(json.dumps(response, indent=2, sort_keys=True))
	print("Verification successful")
	print("Token: "+token)
elif sys.argv[1] == "show":
	token = sys.argv[2]
	vehicleJSON = reqVehicles(token)
	exitOnError(vehicleJSON)
	
	scootinfo = filterScooters(vehicleJSON)

	#print all in json
	print(json.dumps(scootinfo, indent=2, sort_keys=True))

	#print id and google maps location link
	for scoot in scootinfo:
		print(str(scoot["id"]) + ": https://maps.google.com?q="+str(scoot["lat"]) + "," + str(scoot["lng"]))
elif sys.argv[1] == "honk":
	token = sys.argv[2]
	sid = int(sys.argv[3])

	#Verify id exists by requesting vehicles and searching for it
	print("Verifying that the id exists")
	vehicles = reqVehicles(token)
	exitOnError(vehicles)
	scooters = filterScooters(vehicles)
	chosen = None
	for scoot in scooters:
		if scoot["id"] == sid:
			chosen = scoot
			break
	if not chosen:
		print("Could not find scooter with id " + sys.argv[3])
		sys.exit(0)
	print("Scooter found")
	print("Attempting to honk")

	honkResponse = reqHonk(token, chosen)
	exitOnError(honkResponse)
	print("Honk id="+str(chosen["id"])+" at "+str(chosen["lat"])+","+str(chosen["lng"])+" successful")
