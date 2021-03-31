import os, sys


from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *

import random

def create_customer_profile():

    merchantAuth = apicontractsv1.merchantAuthenticationType()
    merchantAuth.name = "979FeLuLX"
    merchantAuth.transactionKey = "42993v965XRbwtKx"


    createCustomerProfile = apicontractsv1.createCustomerProfileRequest()
    createCustomerProfile.merchantAuthentication = merchantAuth
    createCustomerProfile.profile = apicontractsv1.customerProfileType('jdoe' + str(random.randint(0, 10000)), 'John2 Doe', 'jdoe@mail.com')

    controller = createCustomerProfileController(createCustomerProfile)
    controller.execute()

    response = controller.getresponse()

    if (response.messages.resultCode=="Ok"):
        print("Successfully created a customer profile with id: %s" % response.customerProfileId)
    else:
        print("Failed to create customer payment profile %s" % response.messages.message[0]['text'].text)

    return response

create_customer_profile()