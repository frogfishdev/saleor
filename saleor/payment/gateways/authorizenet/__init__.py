import uuid
from decimal import Decimal
import time

from authorizenet import apicontractsv1
from authorizenet.apicontrollers import createTransactionController, getTransactionDetailsController

from ... import ChargeStatus, TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData, PaymentMethodInfo

from .... import settings

from .errors import DEFAULT_ERROR_MESSAGE, AuthorizeNetException

def authorizenet_success():
    return True

# don't need to generate real client token for authorize.net
# the same one just sits in the javascript for every transaction
def get_client_token(**_):
    return str(uuid.uuid4())


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    # add for exising customer

    result, error = transaction_for_customer(payment_information, config)
    suc = False
    if error is None:
        suc = True
    
    kind = TransactionKind.CAPTURE
    credit_card = result.get("credit_card", {})
    
    return GatewayResponse(
        is_success=suc,
        action_required=False,
        kind=kind,
        amount=result.get("amount", payment_information.amount),
        currency=payment_information.currency,
        # customer_id=result.get("customer_id"),
        transaction_id=result.get(
            "transaction_id", payment_information.token
        ),
        error=error,
        payment_method_info=PaymentMethodInfo(
            last_4=credit_card.get("last_4"),
            exp_year=credit_card.get("expiration_year"),
            exp_month=credit_card.get("expiration_month"),
            brand=credit_card.get("card_type", "").lower(),
            name=credit_card.get("cardholder_name"),
            type="card",
        ),
    )



def transaction_for_customer(
    payment_information: PaymentData, config: GatewayConfig
):
    merchant_auth = apicontractsv1.merchantAuthenticationType()
    merchant_auth.name = settings.AUTHORIZENET_API_LOGIN_ID
    merchant_auth.transactionKey = settings.AUTHORIZENET_TRANSACTION_KEY
    
    ref_id = str("ref {}".format(time.time())).split('.')[0]

    # Create the payment object for a payment nonce
    opaque_data = apicontractsv1.opaqueDataType()
    opaque_data.dataDescriptor = "COMMON.ACCEPT.INAPP.PAYMENT"
    opaque_data.dataValue = payment_information.token

    # Add the payment data to a paymentType object
    payment_one = apicontractsv1.paymentType()
    payment_one.opaqueData = opaque_data
    
    # Create order information
    order = apicontractsv1.orderType()
    order.invoiceNumber = str(payment_information.payment_id)
    order.description = payment_information.customer_email
    
    # Set the customer's Bill To address
    customer_address = apicontractsv1.customerAddressType()
    customer_address.firstName = payment_information.billing.first_name
    customer_address.lastName = payment_information.billing.last_name
    customer_address.company = payment_information.billing.company_name
    customer_address.address = payment_information.billing.street_address_1
    customer_address.city = payment_information.billing.city
    customer_address.state = payment_information.billing.country_area
    customer_address.zip = payment_information.billing.postal_code
    customer_address.country = payment_information.billing.country
    
    # Set the customer's identifying information
    customer_data = apicontractsv1.customerDataType()
    customer_data.type = "individual"
    customer_data.email = payment_information.customer_email
    
    # Add values for transaction settings
    duplicate_window_setting = apicontractsv1.settingType()
    duplicate_window_setting.settingName = "duplicateWindow"
    duplicate_window_setting.settingValue = "600"
    settingss = apicontractsv1.ArrayOfSetting()
    settingss.setting.append(duplicate_window_setting)

    # Create a transactionRequestType object and add the previous objects to it
    transactionrequest = apicontractsv1.transactionRequestType()
    transactionrequest.transactionType = "authCaptureTransaction"
    transactionrequest.amount = payment_information.amount
    transactionrequest.order = order
    transactionrequest.payment = payment_one
    transactionrequest.billTo = customer_address
    transactionrequest.customer = customer_data
    transactionrequest.transactionSettings = settingss

    # Assemble the complete transaction request
    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchant_auth
    createtransactionrequest.refId = ref_id
    createtransactionrequest.transactionRequest = transactionrequest
    
    # Create the controller and get response
    createtransactioncontroller = createTransactionController(createtransactionrequest)
    # createtransactioncontroller.setenvironment('https://api2.authorize.net/xml/v1/request.api')
    createtransactioncontroller.execute()

    response = createtransactioncontroller.getresponse()

    error = None
    ret = {}
    
    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages'):
                print ('Successfully created transaction with Transaction ID: %s' % response.transactionResponse.transId)
                print ('Transaction Response Code: %s' % response.transactionResponse.responseCode)
                print ('Message Code: %s' % response.transactionResponse.messages.message[0].code)
                print ('Description: %s' % response.transactionResponse.messages.message[0].description)
            else:
                print ('Failed Transaction.')
                if hasattr(response.transactionResponse, 'errors'):
                    print ('Error Code:  %s' % str(response.transactionResponse.errors.error[0].errorCode))
                    print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText)
                    error = response.transactionResponse.errors.error[0].errorText
        else:
            print ('Failed Transaction.')
            if hasattr(response, 'transactionResponse') and hasattr(response.transactionResponse, 'errors'):
                print ('Error Code: %s' % str(response.transactionResponse.errors.error[0].errorCode))
                print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText)
                error = response.transactionResponse.errors.error[0].errorText
            else:
                print ('Error Code: %s' % response.messages.message[0]['code'].text)
                print ('Error message: %s' % response.messages.message[0]['text'].text)
                error = response.messages.message[0]['text'].text

        if error is None:
            ret = {
                "transaction_id": str(response.transactionResponse.transId) + '---' + payment_information.token,
                "credit_card": {
                    "last_4": str(response.transactionResponse.accountNumber).replace('X', ''),
                    "brand": str(response.transactionResponse.accountType).lower(),
                    "cardholder_name": payment_information.billing.first_name + ' ' + payment_information.billing.last_name,
                    "expiration_year": '09',
                    "expiration_moneth": '23',
                },
            }
    else:
        print ('Null Response.')

    return ret, error




def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    merchant_auth = apicontractsv1.merchantAuthenticationType()
    merchant_auth.name = settings.AUTHORIZENET_API_LOGIN_ID
    merchant_auth.transactionKey = settings.AUTHORIZENET_TRANSACTION_KEY
    t_id = payment_information.token.split('---')[0]

    transactionrequest = apicontractsv1.transactionRequestType()
    transactionrequest.transactionType = "voidTransaction"
    transactionrequest.refTransId = t_id

    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchant_auth
    createtransactionrequest.refId = str("ref {}".format(time.time())).split('.')[0]

    createtransactionrequest.transactionRequest = transactionrequest
    createtransactioncontroller = createTransactionController(createtransactionrequest)
    createtransactioncontroller.execute()

    response = createtransactioncontroller.getresponse()

    error = None
    
    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages'):
                print ('Successfully created transaction with Transaction ID: %s' % response.transactionResponse.transId)
                print ('Transaction Response Code: %s' % response.transactionResponse.responseCode)
                print ('Message Code: %s' % response.transactionResponse.messages.message[0].code)
                print ('Description: %s' % response.transactionResponse.messages.message[0].description)
            else:
                print ('Failed Transaction.')
                if hasattr(response.transactionResponse, 'errors'):
                    print ('Error Code:  %s' % str(response.transactionResponse.errors.error[0].errorCode))
                    print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText)
                    error = str(response.transactionResponse.errors.error[0].errorText)
        else:
            print ('Failed Transaction.')
            if hasattr(response, 'transactionResponse') and hasattr(response.transactionResponse, 'errors'):
                print ('Error Code: %s' % str(response.transactionResponse.errors.error[0].errorCode))
                print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText)
                error = str(response.transactionResponse.errors.error[0].errorText)
            else:
                print ('Error Code: %s' % response.messages.message[0]['code'].text)
                print ('Error message: %s' % response.messages.message[0]['text'].text)
                error = str(response.messages.message[0]['text'].text)
    else:
        print ('Null Response.')
        error = 'No response'

    suc = False 
    if error is None:
        suc = True

    return GatewayResponse(
        is_success=suc,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency='USD',
        transaction_id=t_id,
        error=error,
    )


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    merchant_auth = apicontractsv1.merchantAuthenticationType()
    merchant_auth.name = settings.AUTHORIZENET_API_LOGIN_ID
    merchant_auth.transactionKey = settings.AUTHORIZENET_TRANSACTION_KEY
    t_id = payment_information.token.split('---')[0]

    transaction_details_request = apicontractsv1.getTransactionDetailsRequest()
    transaction_details_request.merchantAuthentication = merchant_auth
    transaction_details_request.transId = t_id

    transaction_details_controller = getTransactionDetailsController(transaction_details_request)

    transaction_details_controller.execute()

    transaction_details_response = transaction_details_controller.getresponse()

    credit_card = apicontractsv1.creditCardType()
    credit_card.cardNumber = str(transaction_details_response.transaction.payment.creditCard.cardNumber).replace('X', '')
    credit_card.expirationDate = "XXXX"

    # Add the payment data to a paymentType object
    payment_one = apicontractsv1.paymentType()
    payment_one.creditCard = credit_card

    transaction_request = apicontractsv1.transactionRequestType()
    transaction_request.transactionType = "refundTransaction"
    transaction_request.amount = payment_information.amount
    #set refTransId to transId of a settled transaction
    transaction_request.refTransId = t_id
    transaction_request.payment = payment_one


    create_transaction_request = apicontractsv1.createTransactionRequest()
    create_transaction_request.merchantAuthentication = merchant_auth
    create_transaction_request.refId = str("ref {}".format(time.time())).split('.')[0]

    create_transaction_request.transactionRequest = transaction_request
    create_transaction_controller = createTransactionController(create_transaction_request)
    # create_transaction_controller.setenvironment('https://api2.authorize.net/xml/v1/request.api')
    create_transaction_controller.execute()

    response = create_transaction_controller.getresponse()

    error = None
    
    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages'):
                print ('Successfully created transaction with Transaction ID: %s' % response.transactionResponse.transId)
                print ('Transaction Response Code: %s' % response.transactionResponse.responseCode)
                print ('Message Code: %s' % response.transactionResponse.messages.message[0].code)
                print ('Description: %s' % response.transactionResponse.messages.message[0].description)
            else:
                print ('Failed Transaction.')
                if hasattr(response.transactionResponse, 'errors'):
                    print ('Error Code:  %s' % str(response.transactionResponse.errors.error[0].errorCode))
                    print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText)
                    error = str(response.transactionResponse.errors.error[0].errorText)
        else:
            print ('Failed Transaction.')
            if hasattr(response, 'transactionResponse') and hasattr(response.transactionResponse, 'errors'):
                print ('Error Code: %s' % str(response.transactionResponse.errors.error[0].errorCode))
                print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText)
                error = str(response.transactionResponse.errors.error[0].errorText)
            else:
                print ('Error Code: %s' % response.messages.message[0]['code'].text)
                print ('Error message: %s' % response.messages.message[0]['text'].text)
                error = str(response.messages.message[0]['text'].text)
    else:
        print ('Null Response.')

    gateway_response = {
        "amount": payment_information.amount,
        "currency": "USD",
        "transaction_id": t_id
    }

    return GatewayResponse(
        is_success=True if error is None else False,
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=gateway_response.get("amount", payment_information.amount),
        currency=gateway_response.get("currency", payment_information.currency),
        transaction_id=gateway_response.get(
            "transaction_id", payment_information.token
        ),
        error=error,
        raw_response=gateway_response,
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process the payment."""
    auth_resp = authorize(payment_information, config)
    return auth_resp



# payments default to auto capture for authorize.net this is just the dummy code
def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform capture transaction."""
    error = None
    success = authorizenet_success()
    if not success:
        error = "Unable to process capture"

    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
        payment_method_info=PaymentMethodInfo(
            last_4="1234",
            exp_year=2222,
            exp_month=12,
            brand="dummy_visa",
            name="Holder name",
            type="card",
        ),
    )