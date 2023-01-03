import requests
import json
import csv
import secrets

# get schedules - will need one for eps as well
schedules_url = "https://api.pagerduty.com/schedules"
schedules_querystring = {"include[]":"schedule_layers", "limit": "5", "offset": 0,}
eps_url = "https://api.pagerduty.com/escalation_policies"
eps_querystring = {"limit": "5", "offset": 0,}
headers = {
    "Content-Type": "application/json",
    "Accept": "application/vnd.pagerduty+json;version=2",
    "Authorization": secrets.PROD_API,
}

# Looping through API calls and offsetting until false
list_of_schedules = []
while True:
    response = requests.request("GET", schedules_url, headers=headers, params=schedules_querystring)
    list_of_schedules.extend(response.json()["schedules"])
    if response.json()["more"] is False:
        break
    schedules_querystring["offset"] += 5

list_of_eps = []
while True:
    response = requests.request("GET", eps_url, headers=headers, params=eps_querystring)
    list_of_eps.extend(response.json()["escalation_policies"])
    if response.json()["more"] is False:
        break
    eps_querystring["offset"] += 5

# Serializing and writing to services.json - used for testing display only
json_object = json.dumps(list_of_eps, indent=4)
with open("services.json", "w") as outfile:
    outfile.write(json_object)

# # CSV writer - opens a csv with defined fields to be written to
with open("inactive_users.csv", "w", newline="") as csvfile:
    fieldnames = ["schedule_name","html_url","deleted_user","deleted_at","user_url"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writerow({"schedule_name" : "Schedule/EP Name", "html_url" : "Schedule/EP URL", "deleted_user" : "Deleted User", "deleted_at": "Deleted At", "user_url": "User URL"})
    # Loop through list of schedule layers, pulling out null values for self reference in users list - complete
    for each_schedule in list_of_schedules:
        layer_list = each_schedule["schedule_layers"]
        for each_layer in layer_list:
            user_list = each_layer["users"]
            for each_user in user_list:
                if each_user["user"]["self"] is None:
                    writer.writerow({"schedule_name" : each_schedule["name"], "html_url" : each_schedule["html_url"], "deleted_user" : each_user["user"]["summary"], "deleted_at": each_user["user"]["deleted_at"], "user_url": each_user["user"]["html_url"]})
    # Loop through EPs - getting null values for targets
    for each_ep in list_of_eps:
        rule_list = each_ep["escalation_rules"]
        for each_rule in rule_list:
            target_list = each_rule["targets"]
            for each_target in target_list:
                if each_target["self"] is None and each_target["type"] == "user_reference":
                    writer.writerow({"schedule_name" : each_ep["summary"], "html_url" : each_ep["html_url"], "deleted_user" : each_target["summary"], "deleted_at": each_target["deleted_at"], "user_url": each_target["html_url"]})