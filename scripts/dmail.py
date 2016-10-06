from mail import simpleemail
from mail import sendadvancedemail
from dparser_live_July import ftp_parser
from dparser_live_July import extract_info
from dhtmlFormer import dhtmlFormmaker
import time
import yahoo_finance

import os
import urllib2
import mysql.connector
from mysql.connector import errorcode
import sys
import feedparser

def live(current):
    newcurrent = []
    links = []
    feed = feedparser.parse("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=SC%2013D&company=&dateb=&owner=exclude&start=0&count=50&output=atom")
    for item in feed.entries:
        if '(Subject)' in item['title']:
            form_type = item['category']
            if form_type =='SC 13D':
                line = item['links'][0]
                RSSlinks = line['href']
                RSSlinks = RSSlinks.rsplit('/',3)
                access = RSSlinks[-1][:-10]
                access = access.replace("-","")
                #print ("access is" + str(access))
                category = 'http://www.sec.gov/Archives/edgar/data/'+ RSSlinks[1] + '/' + RSSlinks[-1][:-10] + '.txt'
                if access not in current:
                    #print ("access is" + str(access))
                    newcurrent.append(access)
                    links.append(category)
    return links, newcurrent

def autorun(current):
    
    links = []
    for i in range(5):
        try:    
            #FTP = ftp_parser()
            links, newcurrent = live(current)
            break
        except Exception as e:
            print e
            time.sleep(5)
    maker = dhtmlFormmaker()
    newcurrent = []

    cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
        password= 'yangfan19931001', database='SC13D')
    cursor = cnx.cursor()
    add_column = ("INSERT INTO 13D_form_testq "
        "(accessNum, acceptedDate, acceptedTime, fileDate, formType, subjectCik, subjectName, subjectSymbol, filedCik, filedName, filedSymbol, CUSIP, fiscalYearEnd, siClass, siClassNum, sourceofFund, AggregateAmount, PercentAmount, txtlink, htmllink, market_cap) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

    for link in links:
        result = extract_info(link) 
        
        subjectCik = result[5]
        url = 'http://yahoo.brand.edgar-online.com/default.aspx?cik=' + str(subjectCik)
        try:
            data = urllib2.urlopen(url).read()
        except Exception as e:
            print e
        
        print('subjectCik is:' + str(subjectCik))
        if data:       
            r = data.split('\n')[144]
            if (r.strip().startswith('<span id="ctl00_cphColBottom_ucSearchFilingResults1_lblTableTop">')):
                core = r.split('>')[1]
                core = core.split('<')[0]
                if core.strip() == '':
                    subjectSymbol = 'NONE'
                else:
                    core = core.rsplit('(',1)[0].strip()
                    subjectSymbol = core.split(':')[1].strip()
        else:
            subjectSymbol = 'NONE'


        filedSymbol = 'NONE'
        
        result = list(result)
        result.insert(7, subjectSymbol)
        result.insert(10, filedSymbol)
        #print result

        print(subjectSymbol)
        if (subjectSymbol != 'NONE'):
            yahoo = yahoo_finance.Share(subjectSymbol)
            yahoo.refresh()
            market_cap = yahoo.get_market_cap()
            if market_cap is None:
                market_cap = 'NA'
        else:
            market_cap = 'NA'
        result.append(market_cap)
        result = tuple(result)

        try:
            cursor.execute(add_column, result)
            newcurrent.append(result[0])
            print("insertion is done")
        except Exception as e:
            print e
        cnx.commit()
        

        html,optimizationFlag,textAnalysisFlag1,textAnalysisFlag2,textAnalysisFlag3 = maker.makeWA(result)
        print("html is done")


        if optimizationFlag == 1:
            optimizationAlert = 'Optimization/'
        else:
            optimizationAlert = ''

        if textAnalysisFlag1 == 1:
            W1Alert = '1Word/'
        else:
            W1Alert = ''

        if textAnalysisFlag2 == 1:
            W2Alert = '2Word/'
        else:
            W2Alert = ''

        if textAnalysisFlag3 == 1:
            W3Alert = '3Word'
        else:
            W3Alert = ''

        Alert = ' '+optimizationAlert+W1Alert+W2Alert+W3Alert+" : "
        if Alert!=' : ':
            Alert = '!!'+Alert

        sendmail = False
        #print html
        #sendadvancedemail("Tracking the 13D parser wrongness", "send email", "") 
        if market_cap == 'NA':
            market_cap = 'NA'
            sendmail = True
        elif market_cap.endswith("M"):
            market_cap = market_cap.split('.')[0]
            if (int(market_cap) >= 50):
                market_cap += "M"
                sendmail = True
        elif market_cap.endswith("B"):
            market_cap = market_cap.split('.')[0] + "B"
            sendmail = True
        else:
            market_cap = market_cap.split('.')[0]
            if int(market_cap) >= 1000:
                market_cap = str(int(market_cap)/1000) + "k"
        print("sending email")
        if int(float(result[17])) == 0 and int(result[16]) == 0 and sendmail:
            sendadvancedemail("13D" + Alert + subjectSymbol + ": " + str(result[17]) + "%, $" + str(market_cap) + " Could not Parse", " ", html)
        elif int(float(result[17])) == 0 and sendmail:
            sendadvancedemail("13D" + Alert + subjectSymbol + ": " + str(result[17]) + "%, $" + str(market_cap) + " Percent Parsed Wrongness", " ", html)
        elif int(result[16]) == 0 and sendmail:
            sendadvancedemail("13D" + Alert + subjectSymbol + ": " + str(result[17]) + "%, $" + str(market_cap) + " Amount Parsed Wrongness", " ", html)
        #elif result[11] == '000000000' and sendmail:
        #    sendadvancedemail("13D" + Alert + subjectSymbol + ": " + str(result[17]) + "%, $" + str(market_cap)  + " CUSIP Parsed Wrongness", " ", html)
        elif sendmail:
            sendadvancedemail("13D" + Alert + subjectSymbol + ": " + str(result[17]) + "%, $" + str(market_cap), " ", html)
        print("fininshing sending email")
                    
    
    cursor.close()
    cnx.close()
    #try:
    #    FTP.disconnect()
    #except Exception as e:
    #    print e
    return current + newcurrent



if __name__ == "__main__":
    cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
        password= 'yangfan19931001', database='fan_new')
    cursor = cnx.cursor()
    select_access = ("SELECT accessNum FROM 13D_form_testq")
    cursor.execute(select_access)
    data = cursor.fetchall()
    cursor.close()
    cnx.close()
    current = list(data)
    current = [entity[0] for entity in current]
    print current
    
    #while (1):
    current = autorun(current)
    time.sleep(60)
    
    #test()




