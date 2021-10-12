# honk
A python command line tool that rings Bolt scooters

### How it works ###
The tool communicates directly with bolt.eu's API's so that it tells it to ring a scooter of your choice. It is required that you generate an authentication token beforehand that is associated with a phone number otherwise the API will reject the request.

### Usage ###
Honk scooter:
```console
python3 honk.py honk [token] [scooter id]
```

Show list of scooters
```console
python3 honk.py show [token]
```

Generate token by sms:
```console
python3 honk.py gentoken [phone number]
```

### Dependencies ###
The script requires the **requests** library. Tested on version 2.25.1

### Disclaimer ###
Use at your own risk. This tool has only been tested in Malta and it contains hard coded values related to the country. There is no guarantee it will work since the API can change anytime.
