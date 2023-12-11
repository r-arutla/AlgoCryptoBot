#https://www.youtube.com/watch?v=xy4gpC4rCZ8

#import requests

#for time.sleep()
import time
#for data analysis
import pandas as pd
#for binance
from binance.client import Client
from binance.exceptions import BinanceAPIException
# for sending email
from email.message import EmailMessage
import ssl
import smtplib
#for reading email
import imaplib
import imap_tools
from imap_tools import MailBox, AND
#for stopping the program using sys.exit()
import sys
#for battery info
import psutil
#for printing error message in error handling
import traceback

apikey = ""
secretkey = ""

testapikey = ""
testsecretkey = ""

#if using testNet, do testnet=True in Client
#client = Client(apikey, secretkey, tld='us', testnet=False)
    

def sendEmail(emailSubject, emailContent):
    sender = 'rohan.arutla@gmail.com'
    password = ''

    receiver = 'rohan.trade.updates@gmail.com'

    subject = emailSubject
    content = emailContent

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(content)

    sslcontext = ssl.create_default_context()

    #465 is the port u need to use for gmail smtp
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=sslcontext) as email:
        email.login(sender, password)
        email.sendmail(sender, receiver, msg.as_string())



    
    
client = Client(testapikey, testsecretkey, tld='us', testnet=True)


def readEmail(symbol, i, in_position):
    username = 'rohan.trade.inputs@gmail.com'
    password = ''
    imap_server = 'imap.gmail.com'
        
    mb = MailBox(imap_server)
    mb.login(username, password)
    
    messages = mb.fetch(criteria=AND(seen=False), mark_seen=False, bulk = False)
    
    for mail in messages:
        
        sender = str(mail.from_)
        emailSubject = str(mail.subject)
        print(emailSubject)
        print(sender)
        
        
        if sender == 'rohan.arutla@gmail.com' or 'rohan.trade.updates@gmail.com':
            
            if emailSubject == "SELL":
                subject = "SELL COMMAND EXECUTED"
                content = "SELL command was executed"
                sendEmail(subject, content)
                
                in_position = sellone(symbol, i)                
                
                
            elif emailSubject == "BUY":
                subject = "BUY COMMAND EXECUTED"
                content = "BUY command was executed"
                sendEmail(subject, content)
                
                in_position = buyone(symbol, i)
                
            elif emailSubject == "STOP" or emailSubject == "QUIT":
                #finish this
                subject = "PROGRAM STOPPED"
                content = "QUIT command executed."
                sendEmail(subject, content)
                
                mb.flag(mail.uid, imap_tools.MailMessageFlags.SEEN, True)
                
                sys.exit()
                
            elif emailSubject == "PRICE CHECK":
                allPrices = client.get_all_tickers()

                for i in allPrices:
                    if i['symbol'] == symbol:
                        price = float(i["price"])
                        
                subject = "ETHUSDT Price: " + str(price)
                content = "Price Check successfully completed.\nETHUSDT Price: " + str(price)
                sendEmail(subject, content)
                
            elif emailSubject == "RUN CHECK":
                
                subject = "Program is still running."
                content = "Run check completed, the program is still running."
                battery = psutil.sensors_battery() 
                if battery != None:
                    percentage = str(battery.percent)
                    content += "\nSystem Battery: " + percentage +"%"
                sendEmail(subject, content)
                
            else:
                subject = "UNRECOGNIZED COMMAND"
                content = "The command entered was not recognized."
                sendEmail(subject, content)
        else:
            subject = "UNRECOGNIZED SENDER"
            content = "An email from an unrecognized sender has been received."
            sendEmail(subject, content)
                
        mb.flag(mail.uid, imap_tools.MailMessageFlags.SEEN, True)
        
    return in_position
        
        

#code for placing a buy order
def buyone(Symbol, iteration):
    order = client.create_order(symbol='ETHUSDT', side='BUY', type='MARKET', quantity=1)
    
    orderstatus = order["status"]
    
    if orderstatus == 'FILLED':
        in_position = True
        buyprice = float(order["fills"][0]["price"])
        stoploss_anchor = buyprice
                        
        #email
        subject = "BUY order FILLED: " + str(buyprice)
        content = "buy order placed \nstatus: " + orderstatus + "\n" + "price: " + str(buyprice)
        sendEmail(subject, content)
                        
        #local printout
        print("iteration: " + str(iteration))
        print("buy order placed")
        print("status:")
        print(orderstatus)
        print("price:")
        print(buyprice)
        print("\n")
        
        output = [in_position, buyprice, stoploss_anchor]
            
    else:
        in_position = False            
        #email
        subject = "BUY order FAILED"
        content = "buy order status: " + orderstatus
        sendEmail(subject, content)
                        
        #local printout
        print("iteration: " + str(iteration))
        print("buy order failed")
        print("order status:")
        print(orderstatus)
        print("\n")
        
        output = False
    return output


def sellone(Symbol, iteration):
    order = client.create_order(symbol='ETHUSDT', side='SELL', type='MARKET', quantity=1)
    
    orderstatus = order["status"]
                    
    if orderstatus == 'FILLED':
        in_position = False
        
        
        sellprice = float(order["fills"][0]["price"])
                        
        #email
        subject = "SELL order FILLED: " + str(sellprice)
        content = "sell order placed \nstatus: " + orderstatus + "\n" + "price: " + str(sellprice)
        sendEmail(subject, content)
                        
        #local printout
        print("iteration: " + str(iteration))
        print("sell order placed")
        print("status:")
        print(orderstatus)
        print("price:")
        print(sellprice)
        print("\n")
                        
                        
    else:
        in_position = True
        #email
        subject = "SELL order FAILED"
        content = "SELL order status: " + orderstatus
        sendEmail(subject, content)
                        
        #local printout
        print("iteration: " + str(iteration))
        print("sell order failed")
        print("order status:")
        print(orderstatus)
        print("\n")
        
    return in_position



def getdata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol, '1m', '20 m ago UTC'))
    frame = frame[[0,1,2,3,4,5]]
    frame.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame.Date = pd.to_datetime(frame.Date, unit='ms')
    frame.set_index('Date', inplace=True)
    frame = frame.astype(float)
    return frame



def runstrategy(symbol, in_position=False, batteryWarning5=False, batteryWarning25=False):
    client = Client(testapikey, testsecretkey, tld='us', testnet=True)
    i = 1
    while True:
        try:
            #system battery check and email warning
            battery = psutil.sensors_battery() 
            if (battery != None):
                percentage = battery.percent
                charging = battery.power_plugged
                if percentage <= 5 and batteryWarning5 == False and charging == False:
                    subject = "LOW BATTERY WARNING"
                    content = "Battery is at " + str(percentage) + "%.\n"
                    content += "Charge the laptop."
                    sendEmail(subject, content)
                    batteryWarning5 == True
                elif percentage <= 25 and batteryWarning25 == False and charging == False:
                    subject = "LOW BATTERY WARNING"
                    content = "Battery is at " + str(percentage) + "%.\n"
                    content += "Charge the laptop."
                    sendEmail(subject, content)
                    batteryWarning25 == True

                if percentage > 5:
                    batteryWarning5 = False
                if percentage > 25:
                    batteryWarning25 = False
            
            
            client = Client(testapikey, testsecretkey, tld='us', testnet=True)
            
            #read email inputs and get the associated return values
            output = readEmail(symbol, i, in_position)
            if str(type(output)) == "<class 'list'>":
                in_position = output[0]
                buyprice = output[1]
                stoploss_anchor = output[2]
            else: 
                in_position = output
            
            #getting data and processing it
            df = getdata(symbol)

            df['tenm_ret'] = df.Close/df.Close.shift(10) - 1
            df['fivem_ret'] = df.Close/df.Close.shift(5) - 1

            df.dropna(inplace=True)
            
            #creating lists out of the required data problems
            ten = df.tenm_ret
            five = df.fivem_ret
            close = df.Close


            #if no coin
            if not in_position:
                if (ten[-1] > 0) & (five[-1] < 0.005):

                    #code for placing a buy order
                    output = buyone(symbol, i)
                    if str(type(output)) == "<class 'list'>":
                        in_position = output[0]
                        buyprice = output[1]
                        stoploss_anchor = output[2]
                        
                    else: 
                        in_position = output
            #if have coin
            if in_position:
                if close[-1] > stoploss_anchor:
                    stoploss_anchor = close[-1]

                if close[-1] < stoploss_anchor*.98 or close[-1] > buyprice*1.015:

                    #code for placing a sell order
                    in_position = sellone(symbol, i)                

            i+=1
            time.sleep(60)
            
        #binance api error handling
        except BinanceAPIException as e:
            
            #email
            subject = "ERROR: BinanceAPI"
            content = "Error:\n" + str(traceback.format_exc()) + "\n\n"+ str(e)
            time.sleep(10)
            sendEmail(subject, content)
            
            #local printout
            print("iteration: " + str(i))
            print("there was a binance api error:")
            print(str(e))
            print("will try again in 60 seconds")
            print("\n")
            
            i+=1
            time.sleep(50)
            
            client = Client(testapikey, testsecretkey, tld='us', testnet=True)
            continue
        
        #all other error handling
        except Exception as e:
            
            #email
            subject = "ERROR: Other"
            content = "Error:\n" + str(traceback.format_exc()) + "\n\n"+ str(e)
            time.sleep(10)
            sendEmail(subject, content)
            
            #local printout
            print("iteration: " + str(i))
            print("something else went wrong:")
            print(str(e))
            print("will try again in 60 seconds")
            print("\n")
            
            i+=1
            time.sleep(50)
            
            client = Client(testapikey, testsecretkey, tld='us', testnet=True)
            continue
        

            


buyorder = buyone('ETHUSDT', 1)
sellorder = sellone('ETHUSDT', 1)


    
#runstrategy('ETHUSDT')
