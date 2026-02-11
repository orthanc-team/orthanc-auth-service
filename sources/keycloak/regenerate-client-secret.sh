#!/bin/bash

# SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0

##########################################################################

# ## Goal

# This script will replace the 'admin-cli' client default secret by
# a freshly generated one and then print it in the logs.

# In the second part of the script, the permissions needed to regenerate
# this secret will be removed.

# ## Usage

# This script is not intended to be ran manually, but it is executed
# during the Keycloak boot sequence and will regenerate the new
# secret only if the read value is the default one.

# ## Notes

# This script being executed to avoid a remaining default secret,
# all the ids needed in the commands are hardcoded.
# It would be more elegant to use grep and other bash tools to parse
# the json answers, but this will be done only if really needed (feel
# the pain as one says).

# The secret value in the script has to be adapted as soon as the Docker
# image is rebuilt.

##########################################################################

cd /opt/keycloak/bin/

# exit if test mode
if [[ ${SKIP_CLIENT_SECRET_UPDATE_FOR_TESTS} == true ]]; then
    echo -e "\n##################################################################################################################"
    echo -e "WARNING ! WARNING ! WARNING ! WARNING !"
    echo -e "Client Secret value is kept to default value!"
    echo -e "This is a major security issue!"
    echo -e "This mode should be used only for unit testing!"
    echo -e "If you read this, you should probably restart your setup withtout the SKIP_CLIENT_SECRET_UPDATE_FOR_TESTS env var"
    echo -e "##################################################################################################################\n"
    exit 0
fi 

# wait till Keycloak is ready

READY=0

while [ $READY -eq 0 ]; do
    # Try to authenticate and capture response
    RESPONSE=$(./kcadm.sh config credentials --server http://localhost:8080 --realm orthanc --client admin-cli --secret THPRqk7LVRVxsxcNnOos3cjtLDfIfh0C 2>&1)
    
    # Wait till Keycloak is ready
    echo "$RESPONSE" | grep -q "Connection refused"
    if [ $? -eq 0 ]; then
        echo "### Keycloak is not ready (Connection refused). Retrying..."
        sleep 3
        continue
    fi

    # If 'Invalid' is part of the response, the secret is already regenerated, so exit
    echo "$RESPONSE" | grep -q "Invalid"
    if [ $? -eq 0 ]; then
        echo "### Access denied with the default secret, probably already regenerated."
        exit 0
    else
        echo "### Keycloak is ready, script authenticated..."
        READY=1
    fi
done

# from here, some lines are commented out (###)
# indeed, as explained above, everything is hardcoded for simplicity purposes
# but if there is a need to improve the script or to get new ids, the logic is here...

# get 'admin-cli' client id:
###./kcadm.sh get clients -r orthanc --fields clientId,id

# regenerate the secret
RESPONSE=$(./kcadm.sh create clients/74a99b9d-221a-4dd1-9ba4-ec4f249c3e0a/client-secret -r orthanc 2>&1)

# if 'error' is part of the response, there is a problem, so warning message
if [[ "$RESPONSE" == *"error"* ]]; then
    echo "### ERROR! Unable to regenerate the secret, maybe some missing permissions..."
fi

# get this new secret
RESPONSE=$(./kcadm.sh get clients/74a99b9d-221a-4dd1-9ba4-ec4f249c3e0a/client-secret -r orthanc 2>&1)

# print the secret
echo -e "\n##########################################################################################"
echo -e "Here is the secret to use for the KEYCLOAK_CLIENT_SECRET env var in the auth service:"
echo -e "$RESPONSE" | grep -o '"value" : "[^"]*"' | sed 's/"value" : "\(.*\)"/\1/'
echo -e "##########################################################################################\n"

# get service account user (a kind of account behind the account)
###./kcadm.sh get clients/74a99b9d-221a-4dd1-9ba4-ec4f249c3e0a/service-account-user -r orthanc

# get roles for this account user
###./kcadm.sh get users/35704d57-da75-4d73-81f4-85cd605398f4/role-mappings -r orthanc

# get clientMapping only
###./kcadm.sh get users/35704d57-da75-4d73-81f4-85cd605398f4/role-mappings/clients/34c7489b-ad3c-4483-a523-e578c1c6dc45 -r orthanc

# remove permission manage-clients
RESPONSE=$(./kcadm.sh delete users/35704d57-da75-4d73-81f4-85cd605398f4/role-mappings/clients/34c7489b-ad3c-4483-a523-e578c1c6dc45 -r orthanc -b '[{"id": "f1360e68-78d5-4df1-a7f9-de0db0de8eb7", "name": "manage-clients"}, {"id": "098dc91c-18f2-4b22-a522-cf5ed10315a5", "name": "manage-users"}]' 2>&1)

# error case
if [ ${#RESPONSE} -ne 0 ]; then
    echo -e "\n\n##### WARNING ! WARNING ! WARNING !"
    echo -e "\n##### Unable to remove the permissions! Keycloak shoulnd t be used as it is!!\n\n"
    exit 1
fi

exit 0