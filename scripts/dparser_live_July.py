import os
#from DB import *
import time
import sys
import datetime
from dateutil.relativedelta import relativedelta
import ftplib
import urllib2
import feedparser
import re
import gzip
import mysql.connector
from mysql.connector import errorcode
import StringIO
import math
from contextlib import closing
import time

class ftp_parser:

    def __init__(self):
        self.ftp = ftplib.FTP('ftp.sec.gov')
        self.ftp.login()
        daily_index_path = '/edgar/daily-index/'
        self.ftp.cwd(daily_index_path)
        #self.db = database(database.east)

    def disconnect(self):
        self.ftp.close()

    def stream(self, current):
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
                        print ("access is" + str(access))
                        newcurrent.append(access)
                        links.append(category)
        return links, newcurrent

    def findIDX(self, DATE):
        formName = 'form.'+DATE.strftime('%Y%m%d')+'.idx'
        tmp = os.tmpfile()
        try:
            self.ftp.retrbinary('RETR '+formName, tmp.write)
        except Exception as e:
            print e
            return None
        tmp.seek(0)
        print tmp
        return tmp

    def findnewIDX(self, DATE):
        formName = 'form.'+DATE.strftime('%Y%m%d')+'.idx.gz'
        sio = StringIO.StringIO()
        def handle_binary(data):
            sio.write(data)
        try:
            self.ftp.retrbinary('RETR '+formName, callback=handle_binary)
        except Exception as e:
            print e
            return None
        sio.seek(0)
        zippy = gzip.GzipFile(fileobj=sio)
        print zippy
        return zippy

    def parseIDX(self, tmp, parsedForms = set()):
        if tmp == None:
            return []
        links = set()
        newlinks = set()
        start = False

        for line in tmp:
            if start:
                line = line.strip().split()
                if line and line[0] == "SC":
                    if line[1] == "13D" or line[1] == "13D/A" or line[1] == "13G" or line[1] == "13G/A":
                        issuerCik, accessionNumber = (line[-1].strip())[11:-4].split('/')
                        if accessionNumber not in parsedForms:
                            links.add('https://www.sec.gov/Archives/edgar/data/'+ issuerCik + '/' + accessionNumber + '.txt')
            elif line[:10] == '-'*10:
                start = True
        return links

    def run(self, DATE = datetime.datetime.now().date() - relativedelta(days = 1)):
        tmpFile = self.findIDX(DATE)
        #parsedForms = set(self.db.session.query(form.accessionNumber).filter(form.acceptedDate == DATE).all())
        #self.db.session.commit()
        #return self.parseIDX(tmpFile, parsedForms = parsedForms)
        if not tmpFile:
            tmpFile = self.findnewIDX(DATE)
        return self.parseIDX(tmpFile)

def str2int(str):
    str = str.replace(",", "")
    return int(str)

def str2int2(str):
    str = str.replace("%", "")
    return float(str)

def download(processList):
    count = 0
    for url in processList:
        f = urllib2.urlopen(url)
        data = f.read()
        with open("num"+str(count)+".txt", "wb") as code:
            code.write(data)
        count = count + 1

def extract_info(url):

    print 'processing %s'%url

    for i in range(5):
        try:
            data = urllib2.urlopen(url).read()
            break
        except Exception as e:
            print __name__, e, 'on line ', sys.exc_traceback.tb_lineno
            print url, ' fail, try again %d'%(i+1)
            time.sleep(1.5)

    try:
        data = data.encode('utf8')
    except:
        print "ftp delay exceed"
    SoleVotingPower = []
    SharedVotingPower = []
    SoleDispositivePower = []
    SharedDispositivePower = []
    AggregateAmount = []
    PercentAmount = []
    sourceofFund = 'NA'
    CUSIP = '000000000'
    subject = False
    header = True
    ender = False
    SharedVPPart = False
    SoleVPPart = False
    SharedDPPart = False
    SoleDPPart = False
    AggPart = False
    PerPart = False
    SoleVPSearch = False
    SoleVPSearch = False
    SharedDPSearch = False
    SoleDPSearch = False
    AggSearch = False
    PerSearch = False
    counter = 0
    findSource = False
    fisExist = False
    siExist = False
    findCUSIP = True
    findName = True
    #s = re.compile('[\d]+,[\d]+')
    ss = re.compile('[\d]+,[\d]+,[\d]+')
    sss = re.compile('[\d]+,[\d]+')
    s = re.compile('[\d]+[\.]?[\d]*[ ]?%')
    sp = re.compile('>[\d]+[\.]?[\d]*[ ]?%')
    sd = re.compile('[\d]+[\.]?[\d]*[ ]?%[;"]')
    sf = re.compile('/[\d]+[\.]?[\d]*[ ]?%')
    si = re.compile('Item [\d]\.')
    sii = re.compile('ITEM [\d]\.')
    ssi = re.compile('Item&nbsp;[\d]\.')
    ssii = re.compile('ITEM&nbsp;[\d]\.')
    sip = re.compile('[\w|\*|@|#][\w|\*|@|#][\w|\*|@|#][\w|\*|@|#][\w|\*|@|#][ ]?[\w|\*|@|#][ ]?[\w|\*|@|#][ ]?[\w|\*|@|#][ ]?[\w|\*|@|#]')
    for r in data.split('\n'):
        if r.strip() == '</SEC-HEADER>':
            header = False
            PerPart = True
        if findName and r.startswith('<FILENAME>'):
            fileName = r[10:]
            findName = False
        if header:
            if r.strip() == 'SUBJECT COMPANY:':
                subject = True
            elif r.strip() == 'FILED BY:':
                subject = False
            elif r.startswith('ACCESSION NUMBER'):
                accessNum = r[19:29] + r[30:32] + r[33:]
                print accessNum
            elif r.startswith('<ACCEPTANCE-DATETIME>'):
                acceptedDate = r[21:29]
                acceptedTime = r[29:]
                print acceptedDate
                print acceptedTime
            elif r.startswith('FILED AS OF DATE'):
                fileDate = r[19:27]
                print fileDate
            elif r.strip().startswith('FORM TYPE'):
                formType = r[14:]
                print formType
                if formType == 'SC 13G' or formType == 'SC 13G/A':
                    sourceofFund = 'NA'
            elif r.strip().startswith('STANDARD INDUSTRIAL CLASSIFICATION'):
                siExist = True
                r = r.split('\t')
                sic = r[3]
                sic = sic.split('[')
                siClass = sic[0]
                siClassNum = sic[1][0:-1]
                print siClass
                print siClassNum
            elif r.strip().startswith('FISCAL YEAR END'):
                fisExist = True
                fiscalYearEnd = r.split('\t')
                fiscalYearEnd = fiscalYearEnd[5]
                print fiscalYearEnd
            elif r.strip().startswith('CENTRAL INDEX KEY'):
                if subject == True:
                    subjectCik = r[23:33]
                    print subjectCik
                else:
                    filedCik = r[23:33]
                    print filedCik
            elif r.strip().startswith('COMPANY CONFORMED NAME'):
                if subject == True:
                    subjectName = r[28:]
                    print subjectName
                else:
                    filedName = r[28:]
                    print filedName
        if ender == False and (r.__contains__('Items') or r.__contains__('Item') or r.__contains__('ITEM') or r.__contains__('ITEMS')):
            print "end"
            temp = si.search(r)
            temp1 = ssi.search(r)
            temp2 = sii.search(r)
            temp3 = ssii.search(r)
            if temp or temp1 or temp2 or temp3:
                ender = True
        if header == False and ender == False:
            if findCUSIP:
                sips = sip.findall(r)
                for cuSIP in sips:
                    print cuSIP
                    if check(cuSIP):
                        findCUSIP = False
                        if len(cuSIP) == 9:
                            CUSIP = cuSIP
                        elif len(cuSIP) == 11:
                            CUSIP = cuSIP[0:6] + cuSIP[7:9] + cuSIP[10]
                        elif len(cuSIP) == 10:
                            CUSIP = cuSIP[0:6] + cuSIP[7:10]
                        print CUSIP
                        break
                    if len(cuSIP) == 11:
                        CuSIP = cuSIP[0:5] + cuSIP[6:8] + cuSIP[9:11]
                        if check(CuSIP):
                            findCUSIP = False
                            CUSIP = CuSIP
                            print CUSIP
                            break
          #while (r.__contains__('SOLE') or r.__contains__('Sole') or r.__contains__('SHARED') or r.__contains__('Shared') or r.__contains__('Beneficially Owned') or r.__contains__('BENEFICIALLY OWNED') or r.__contains__('Percent') or r.__contains__('PERCENT')):
            if formType == 'SC 13D' or formType == 'SC 13D/A':
                if r.__contains__('Source') or r.__contains__('SOURCE'):
                    findSource = True
            if findSource:
                if r.__contains__('OO'):
                    sourceofFund = 'OO'
                    findSource = False
                elif r.__contains__('SC'):
                    sourceofFund = 'SC'
                    findSource = False
                elif r.__contains__('BK'):
                    sourceofFund = 'BK'
                    findSource = False
                elif r.__contains__('AF'):
                    sourceofFund = 'AF'
                    findSource = False
                elif r.__contains__('WC'):
                    sourceofFund = 'WC'
                    findSource = False
                elif r.__contains__('PF'):
                    sourceofFund = 'PF'
                    findSource = False
            if (r.__contains__('SOLE') or r.__contains__('Sole')) and PerPart:
                if (r.__contains__('SOLE')):
                    r = r.split('SOLE', 1)[1]
                else:
                    r = r.split('Sole', 1)[1]
                counter = counter+1
                print(counter)
                SoleVPPart = True
                SoleVPSearch = True
                PerPart = False
                if len(SharedDispositivePower) < counter-1:
                    SharedDispositivePower.append(0)
                if len(SoleDispositivePower) < counter-1:
                    SoleDispositivePower.append(0)
                if len(SoleVotingPower) < counter-1:
                    SoleVotingPower.append(0)
                if len(SharedVotingPower) < counter-1:
                    SharedVotingPower.append(0)
                if len(AggregateAmount) < counter-1:
                    if SharedVotingPower[-1] == 0 and SoleDispositivePower[-1] == 0 and SoleVotingPower[-1] == 0 and SharedVotingPower[-1] == 0:
                        AggregateAmount.append(0)
                if len(PercentAmount) < counter-1:
                    if SharedVotingPower[-1] == 0 and SoleDispositivePower[-1] == 0 and SoleVotingPower[-1] == 0 and SharedVotingPower[-1] == 0:
                        PercentAmount.append(0)
            if (r.__contains__('SHARED') or r.__contains__('Shared') or r.__contains__('Shares') or r.__contains__('SHARES') or r.__contains__('SHARE') or r.__contains__('Share')) and SoleVPPart:
                if (r.__contains__('SHARED')):
                    r = r.split('SHARED', 1)[1]
                elif (r.__contains__('Shared')):
                    r = r.split('Shared', 1)[1]
                elif (r.__contains__('SHARES')):
                    r = r.split('SHARES', 1)[1]
                elif (r.__contains__('Shares')):
                    r = r.split('Shares', 1)[1]
                elif (r.__contains__('Share')):
                    r = r.split('Share', 1)[1]
                else:
                    r = r.split('SHARE', 1)[1]
                SharedVPPart = True
                SharedVPSearch = True
                SoleVPPart = False
            if (r.__contains__('SOLE') or r.__contains__('Sole')) and SharedVPPart:
                if (r.__contains__('SOLE')):
                    r = r.split('SOLE', 1)[1]
                else:
                    r = r.split('Sole', 1)[1]
                SoleDPPart = True
                SoleDPSearch = True
                SharedVPPart = False
            if (r.__contains__('SHARED') or r.__contains__('Shared') or r.__contains__('Shares') or r.__contains__('SHARES') or r.__contains__('Share') or r.__contains__('SHARE')) and SoleDPPart:
                if (r.__contains__('SHARED')):
                    r = r.split('SHARED', 1)[1]
                elif (r.__contains__('Shared')):
                    r = r.split('Shared', 1)[1]
                elif (r.__contains__('SHARES')):
                    r = r.split('SHARES', 1)[1]
                elif (r.__contains__('Shares')):
                    r = r.split('Shares', 1)[1]
                elif (r.__contains__('Share')):
                    r = r.split('Share', 1)[1]
                else:
                    r = r.split('SHARE', 1)[1]
                SharedDPPart = True
                SharedDPSearch = True
                SoleDPPart = False
            if (r.__contains__('Aggregate') or r.__contains__('AGGREGATE')) and SharedDPPart:
                if (r.__contains__('AGGREGATE')):
                    r = r.split('AGGREGATE', 1)[1]
                else:
                    r = r.split('Aggregate', 1)[1]
                AggPart = True
                AggSearch = True
                SharedDPPart = False
            if (r.__contains__('Percent') or r.__contains__('PERCENT')) and AggPart:
                if (r.__contains__('PERCENT')):
                    r = r.split('PERCENT', 1)[1]
                else:
                    r = r.split('Percent', 1)[1]
                PerPart = True
                PerSearch = True
                AggPart = False
            if SoleVPPart and SoleVPSearch:
                SoleVP = ss.search(r)
                if SoleVP:
                    SoleVotingPower.append(str2int(SoleVP.group()))
                    SoleVPSearch = False
                else:
                    SoleVP = sss.search(r)
                    if SoleVP:
                        SoleVotingPower.append(str2int(SoleVP.group()))
                        SoleVPSearch = False
            if SharedVPPart and SharedVPSearch:
                SharedVP = ss.search(r)
                if SharedVP:
                    SharedVotingPower.append(str2int(SharedVP.group()))
                    SharedVPSearch = False
                else:
                    SharedVP = sss.search(r)
                    if SharedVP:
                        SharedVotingPower.append(str2int(SharedVP.group()))
                        SharedVPSearch = False
            if SoleDPPart and SoleDPSearch:     
                SoleDP = ss.search(r)
                if SoleDP:
                    SoleDispositivePower.append(str2int(SoleDP.group()))
                    SoleDPSearch = False
                else:
                    SoleDP = sss.search(r)
                    if SoleDP:
                        SoleDispositivePower.append(str2int(SoleDP.group()))
                        SoleDPSearch = False
            if SharedDPPart and SharedDPSearch:
                SharedDP = ss.search(r)
                if SharedDP:
                    SharedDispositivePower.append(str2int(SharedDP.group()))
                    SharedDPSearch = False
                else:
                    SharedDP = sss.search(r)
                    if SharedDP:
                        SharedDispositivePower.append(str2int(SharedDP.group()))
                        SharedDPSearch = False
            if AggPart and AggSearch:
                Agg = ss.search(r)
                if Agg:
                    AggregateAmount.append(str2int(Agg.group()))
                    AggSearch = False
                else:
                    Agg = sss.search(r)
                    if Agg:
                        AggregateAmount.append(str2int(Agg.group()))
                        AggSearch = False
            if PerPart and PerSearch:
                Per = s.findall(r)
                Fail = sd.findall(r)
                Fail2 = sf.findall(r)
                Must = sp.findall(r)
                if Per:
                    if len(Per) == len(Fail):
                        continue
                    else:
                        skip = False
                        for i in range(len(Per)):
                            if '>'+Per[i] in Must:
                                PercentAmount.append(str2int2(Per[i]))
                                PerSearch = False
                                skip = True
                                break
                        if not skip:
                            for i in range(len(Per)):
                                if Per[i]+';' not in Fail and Per[i]+'"' not in Fail and '/'+Per[i] not in Fail2:
                                    PercentAmount.append(str2int2(Per[i]))
                                    PerSearch = False
                                    break  
                                #if i >= len(Fail):
                                #    PercentAmount.append(Per[i])
                                #    PerPart = False
                                #else:
                                #    if Per[i]+';' != Fail[i] and Per[i]+'"' != Fail[i]:
                                #        PercentAmount.append(Per[i])
                                #        PerPart = False
                                #        break
            #elif r.__contains__('Voting') and r.__contains__('Shared'):
            #    SharedVP = r.split('<')[5].split('>')[1].split('(')[0].strip()
            #    SharedVotingPower.append(SharedVP)
            #elif r.__contains__('Voting') and r.__contains__('Sole'):
            #    SoleVP = r.split('<')[5].split('>')[1].split('(')[0].strip()
            #    SoleVotingPower.append(SoleVP)
            #elif r.__contains__('Dispositive') and r.__contains__('Shared'):
            #    SharedDP = r.split('<')[5].split('>')[1].split('(')[0].strip()
            #    SharedDispostitivePower.append(SharedDP)
            #elif r.__contains__('Dispositive') and r.__contains__('Sole'):
            #    SoleDP = r.split('<')[5].split('>')[1].split('(')[0].strip()
            #    SoleDispositivePower.append(SoleDP)
            #elif r.__contains__('Aggregate') and r.__contains__('Owned'):
            #    AA = r.split('<')[5].split('>')[1].split('(')[0].strip()
            #    AggragteAmount.append(AA)
            #elif r.__contains__('Percent'):
            #    PC = r.split('<')[5].split('>')[1].split('(')[0].strip()
            #    PercentAmount.append(PC)
    if len(SharedDispositivePower) < counter:
        SharedDispositivePower.append(0)
    if len(SoleDispositivePower) < counter:
        SoleDispositivePower.append(0)
    if len(SoleVotingPower) < counter:
        SoleVotingPower.append(0)
    if len(SharedVotingPower) < counter:
        SharedVotingPower.append(0)
    if len(AggregateAmount) < counter:
        if SharedVotingPower[-1] == 0 and SoleDispositivePower[-1] == 0 and SoleVotingPower[-1] == 0 and SharedVotingPower[-1] == 0:
            AggregateAmount.append(0)
    if len(PercentAmount) < counter:
        if SharedVotingPower[-1] == 0 and SoleDispositivePower[-1] == 0 and SoleVotingPower[-1] == 0 and SharedVotingPower[-1] == 0:
            PercentAmount.append(0)
    print SoleVotingPower
    print SharedVotingPower
    print SoleDispositivePower
    print SharedDispositivePower
    print AggregateAmount
    print PercentAmount
    print CUSIP
    if not siExist:
        siClass = 'NA'
        siClassNum = '0000'
    if not fisExist:
        fiscalYearEnd = '0000'
    if (len(SoleVotingPower) != 0) and (len(AggregateAmount) != 0) and (len(PercentAmount) != 0 and (len(SoleVotingPower)==len(AggregateAmount)) and (len(SoleVotingPower)==len(PercentAmount))):
        CalAgg, CalPer = calculate(SoleVotingPower, SharedVotingPower, SoleDispositivePower, SharedDispositivePower, AggregateAmount, PercentAmount, url, formType)
        print "CalAgg is " + str(CalAgg)
        print "CalPer is " + str(CalPer)
        if CalPer > 100.0:
            CalPer = 0.0
        html = "https://www.sec.gov/Archives/edgar/data/" + str(int(filedCik)) + "/" + str(accessNum) + "/" + fileName
        print html
        result = [accessNum, acceptedDate, acceptedTime, fileDate, formType, subjectCik, subjectName, filedCik, filedName, CUSIP, fiscalYearEnd, siClass, siClassNum, sourceofFund, CalAgg, CalPer, url, html]
        result = tuple(result) 
        return result
    else:
        html = "https://www.sec.gov/Archives/edgar/data/" + str(int(filedCik)) + "/" + str(accessNum) + "/" + fileName
        print html
        CalPer = 0.0
        CalAgg = 0
        result = [accessNum, acceptedDate, acceptedTime, fileDate, formType, subjectCik, subjectName, filedCik, filedName, CUSIP, fiscalYearEnd, siClass, siClassNum, sourceofFund, CalAgg, CalPer, url, html]
        result = tuple(result)
        return result

def calculate(SoleVotingPower, SharedVotingPower, SoleDispositivePower, SharedDispositivePower, AggregateAmount, PercentAmount, url, formType):
    if len(SoleVotingPower) == 1:
        return AggregateAmount[0], PercentAmount[0]
    identical = True
    for temp in AggregateAmount:
        if temp != AggregateAmount[0]:
            identical = False
    if identical:
        return AggregateAmount[0], PercentAmount[0]
    if len(AggregateAmount) > 20:
        return max(AggregateAmount), max(PercentAmount)
    data = urllib2.urlopen(url).read()
    start = True
    end = False
    Aggresult = []
    Perresult = []
    si = re.compile('Item [\d]\.')
    sii = re.compile('ITEM [\d]\.')
    ssi = re.compile('Item&nbsp;[\d]\.')
    ssii = re.compile('ITEM&nbsp;[\d]\.')
    ss = re.compile('[\d]+,[\d]+,[\d]+')
    sss = re.compile('[\d]+,[\d]+')
    s = re.compile('[\d]+[\.]?[\d]*[ ]?%')
    sd = re.compile('[\d]+[\.]?[\d]*[ ]?%[;"]')
    sf = re.compile('/[\d]+[\.]?[\d]*[ ]?%')
    if formType == 'SC 13D' or formType == 'SC 13D/A':
        for r in data.split('\n'):
            if (r.__contains__('ITEM 5.')) or (r.__contains__('Item 5.')):
                print ("Calculating")
                Aggresult, Perresult = permute(AggregateAmount, PercentAmount)
                start = False
                if (r.__contains__('ITEM 5.')):
                    r = r.split('ITEM 5.', 1)[1]
                else:
                    r = r.split('Item 5.', 1)[1]
            if start == False:
                temp = si.search(r)
                temp1 = sii.search(r)
                temp2 = ssi.search(r)
                temp3 = ssii.search(r)
                if temp or temp1 or temp2 or temp3:
                    end = True
            if start == False and end == False:
                Per = s.findall(r)
                Agg = ss.findall(r)
                Per1 = sd.findall(r)
                Per2 = sf.findall(r)
                # print Agg
                Agg2 = sss.findall(r)
                newAgg = []
                newAgg2 = []
                newPer = []
                # print Agg2
                for num in Agg:
                    newAgg.append(str2int(num))
                for num in Agg2:
                    newAgg2.append(str2int(num))
                for num in Per:
                    if (num+';' not in Per1) and (num+'"' not in Per1) and ('/'+num not in Per2):
                        newPer.append(str2int2(num))
                for i in range(len(Aggresult)):
                    for Aggre in newAgg:
                        if Aggre != 0 and abs(float(Aggre - Aggresult[i])/Aggre) < 0.0001:
                            log = int(math.ceil(math.log(i+1, 2)))
                            if i == int(math.pow(2,log))-1:
                                continue
                            else:
                                if Aggresult[i] > max(AggregateAmount): 
                                    return Aggresult[i], Perresult[i]
                    for Aggre in newAgg2:
                        if Aggre != 0 and abs(float(Aggre - Aggresult[i])/Aggre) < 0.0001:
                            log = int(math.ceil(math.log(i+1, 2)))
                            if i == int(math.pow(2,log))-1:
                                continue
                            else:
                                if Aggresult[i] > max(AggregateAmount): 
                                    return Aggresult[i], Perresult[i]
                    for Percen in newPer:
                        if Percen != 0 and abs(float(Percen - Perresult[i])/Percen) < 0.0001:
                            log = int(math.ceil(math.log(i+1, 2)))
                            if i == int(math.pow(2,log))-1:
                                continue
                            else:
                                if Perresult[i] > max(PercentAmount) and Aggresult[i] > max(AggregateAmount):
                                    return Aggresult[i], Perresult[i]
    elif formType == 'SC 13G' or formType == 'SC 13G/A':
        for r in data.split('\n'):
            if (r.__contains__('ITEM 4.')) or (r.__contains__('Item 4.')):
                print ("Calculating")
                Aggresult, Perresult = permute(AggregateAmount, PercentAmount)
                start = False
                if (r.__contains__('ITEM 4.')):
                    r = r.split('ITEM 4.', 1)[1]
                else:
                    r = r.split('Item 4.', 1)[1]
            if start == False:
                temp = si.search(r)
                temp1 = sii.search(r)
                temp2 = ssi.search(r)
                temp3 = ssii.search(r)
                if temp or temp1 or temp2 or temp3:
                    end = True
            if start == False and end == False:
                Per = s.findall(r)
                Agg = ss.findall(r)
                Per1 = sd.findall(r)
                Per2 = sf.findall(r)
                # print Agg
                Agg2 = sss.findall(r)
                newAgg = []
                newAgg2 = []
                newPer = []
                # print Agg2
                for num in Agg:
                    newAgg.append(str2int(num))
                for num in Agg2:
                    newAgg2.append(str2int(num))
                for num in Per:
                    if (num+';' not in Per1) and (num+'"' not in Per1) and ('/'+num not in Per2):
                        newPer.append(str2int2(num))
                for i in range(len(Aggresult)):
                    for Aggre in newAgg:
                        if Aggre != 0 and abs(float(Aggre - Aggresult[i])/Aggre) < 0.0001:
                            log = int(math.ceil(math.log(i+1, 2)))
                            if i == int(math.pow(2,log))-1:
                                continue
                            else:
                                if Aggresult[i] > max(AggregateAmount):
                                    return Aggresult[i], Perresult[i]
                    for Aggre in newAgg2:
                        if Aggre != 0 and abs(float(Aggre - Aggresult[i])/Aggre) < 0.0001:
                            log = int(math.ceil(math.log(i+1, 2)))
                            if i == int(math.pow(2,log))-1:
                                continue
                            else:
                                if Aggresult[i] > max(AggregateAmount):
                                    return Aggresult[i], Perresult[i]
                    for Percen in newPer:
                        if Percen != 0 and abs(float(Percen - Perresult[i])/Percen) < 0.0001:
                            log = int(math.ceil(math.log(i+1, 2)))
                            if i == int(math.pow(2,log))-1:
                                continue
                            else:
                                if Perresult[i] > max(PercentAmount) and Aggresult[i] > max(AggregateAmount): 
                                    return Aggresult[i], Perresult[i]
    return max(AggregateAmount), max(PercentAmount)

def check(str):
    sum = 0
    if len(str) == 10:
        str =  str[0:6] + str[7:10]
    if len(str) == 11:
        str = str[0:6] + str[7:9] + str[10]
    for i in range(8):
        c = str[i]
        if c.isdigit():
            v = int(c)
        elif c.isupper():
            p = ord(c) - 65 + 1
            v = p + 9
        elif c == '*':
            v = 36
        elif c == '@':
            v = 37
        elif c == '#':
            v = 38
        else:
            return False
        if i % 2 == 1:
            v = v * 2
        sum = sum + v / 10 + v % 10
    check =  (10 - sum % 10) % 10
    if str[8].isdigit() and str[1].isdigit() and str[2].isdigit and str[3].isdigit and check == int(str[8]):
        return True
    else:
        return False

def permute(AggregateAmount, PercentAmount):
    Aggresult = []
    Perresult = []
    newAggregateAmount = []
    newPercentAmount = []
    AggregateAmount.sort()
    PercentAmount.sort()
    for a,b in zip(AggregateAmount, PercentAmount):
        if a != 0 and (a not in newAggregateAmount):
            newAggregateAmount.append(a)
            newPercentAmount.append(b)
    for a,b in zip(newAggregateAmount, newPercentAmount):
        length = len(Aggresult)
        Aggresult.append(a)
        Perresult.append(b)
        for i in range(length):
            Aggresult.append(Aggresult[i] + a)
            Perresult.append(Perresult[i] + b)
    return Aggresult, Perresult

"""
if __name__ == "__main__":
    links = 'http://www.sec.gov/Archives/edgar/data/1636050/0001193125-16-647419.txt'
    form = extract_info(links)
    print form 
"""


if __name__ == "__main__":

    FTP = ftp_parser()
    cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
        password= 'yangfan19931001', database='fan_new')
    cursor = cnx.cursor()
    select_num = ("SELECT accessNum FROM 13D_4 WHERE acceptedDate = '2016-06-01'")
    #date = (datetime.datetime.now().date())
    #cursor.execute(select_num, date)
    cursor.execute(select_num)
    data = cursor.fetchall()
    data = list(data)
    while (1):
        newdata = FTP.stream(data)
        print data
        print newdata
        for record in newdata:
            print record
            if record not in data:
                print(record)
                form = extract_info(record)
                if not form:
                    continue
                add_column = ("INSERT INTO 13D_4 "
                    "(accessNum, acceptedDate, acceptedTime, fileDate, formType, subjectCik, subjectName, filedCik, filedName, CUSIP, fiscalYearEnd, siClass, siClassNum, sourceofFund, AggregateAmount, PercentAmount, txtlink, htmllink) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                try:
                    cursor.execute(add_column, form)
                except Exception as e:
                    print e
                data.append(record)
        cnx.commit()
        time.sleep(30)
    FTP.disconnect()
    

    








