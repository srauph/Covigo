from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
#secret: 7vvLXasNTKxFHOyAEQBYv2o1JURAV3p2
#twilio phone number: +16626727846

account = "AC77b343442a4ec3ea3d0258ea5c597289"
token = "f9a14a572c2ab1de3683c0d65f7c962b"
client = Client(account, token)

try:
    message = client.messages.create(to="+14389263383", from_="+16626727846",
                                 body="Hello there!")
except TwilioRestException as e:
  print(e)
