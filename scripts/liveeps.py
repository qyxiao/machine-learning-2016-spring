import sys
import os
filepath = os.path.dirname(os.path.realpath(__file__))
"""
when it runs on the windows we use the first line. When it runs on the Linux(EC2), we use the second line.
"""
# windows
filepath = filepath.rsplit("\\", 1)[0]
# linux
filepath = filepath.rsplit("/", 1)[0]
sys.path.append(filepath)

from models.DB import database, form, tmpResults, additioninfo
import pdb
import datetime
import time
import myql
import json
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, and_, exc
from models.mail import sendadvancedemail
from models.htmlFormer import epsFormer
from models.criteria import epsCriteria
from models.updatePrice import downLoadPrice
#from models.googlecalendar import Calendar


def catcher(func):
    def wrapper(*arv, **kwargs):
        for i in range(5):
            try:
                func(*arv, **kwargs)
                return func
                break
            except exc.SQLAlchemyError as e:
                print e
                time.sleep(5)

    return wrapper


class epsCik:

    def __init__(self):
        self.period = None
        self.date = None


class downLoadDate(downLoadPrice):

    def getepsdate(self, start_date, end_date):
        """"""
        yql = myql.MYQL(format='json', community=True)
        baseurl = "http://biz.yahoo.com/research/earncal/%s.html"
        xpath = "/html/body/p[3]/table/tbody/tr/td[1]/table[1]/tbody/tr"
        yqlformat = 'SELECT * FROM html WHERE url="%s" and xpath="%s"'

        toDb = {}
        for date in self.daterange(start_date, end_date):
            url = baseurl % (date.strftime("%Y%m%d"))
            rawquery = yqlformat % (url, xpath)
            resp = yql.raw_query(rawquery)
            if not json.loads(resp.content)["query"]["results"]:
                continue
            results = json.loads(resp.content)["query"]["results"]["tr"][2:-1]

            for result in results:
                try:
                    if not result["td"][1]["a"]["content"]:
                        continue
                except Exception as e:
                    print e
                    print date.strftime("%Y%m%d")
                    continue
                issuerSymbol = result["td"][1]["a"]["content"]
                timedata = ""
                for index in range(2, 4):
                    if "small" in result["td"][2]:
                        timedata = result["td"][2]["small"]
                        break

                cik = epsCik()
                cik.period = timedata
                cik.date = date
                toDb[issuerSymbol] = cik
        return toDb


class epsFilter():
    """"""

    def __init__(self):
        self.db = database(database.east)
        self.step = 100
        self.gap = 15
        self.url = 'http://ec2-54-173-27-219.compute-1.amazonaws.com/lmg_app//search/?numofrows=50&'
        self.now = datetime.datetime.now().date()
        self.begDate = self.now - relativedelta(weeks=1)
        self.checker = epsCriteria()
        self.former = epsFormer()
        self.calendar = Calendar()
        self.epsdates = downLoadDate().getepsdate(
            self.now -
            relativedelta(
                weeks=1),
            self.now +
            relativedelta(
                weeks=2))
        self.formsbuyDict = {'forms': {'GB': None, 'LB': None, 'FB': None, 'BR': None, 'WA': None},
                             'dayclass': {'GB': None, 'LB': None, 'FB': None, 'BR': None, 'WA': None}}
        self.formssellDict = {'forms': {'SR': None, 'WAS': None},
                              'dayclass': {'SR': None, 'WAS': None}}

    #----------------------------------------------------------------------
    def run(self):
        """"""
        # filter
        self.roughFilter()
        html = self.filter()

        # add calendar & reminder of currently unavailable ciks
        html += self.addCalendar()

        # send email
        sendadvancedemail("*EPS Summary From " +
                          str(self.begDate) +
                          " To " +
                          str(self.now), None, html)

    def addCalendar(self):
        """Use google API in models.googlecalendar to add reminder"""
        nullIssuers = set()
        rlsdIssuers = set()
        notAvlTemp = "<br>%s</br>"
        AvlTemp = "<br>%s\t\t\t%s\t\t\t%s</br>"

        # get eps dates
        for key, forms in self.formsbuyDict['forms'].items():
            for f in forms:
                if f.issuerTradingSymbol in self.epsdates:
                    ec = self.epsdates[f.issuerTradingSymbol]
                    self.calendar.main(key, f, ec)
                    rlsdIssuers.add((f.issuerTradingSymbol, ec))
                else:
                    nullIssuers.add(f.issuerTradingSymbol)

        for key, forms in self.formssellDict['forms'].items():
            for f in forms:
                if f.issuerTradingSymbol in self.epsdates:
                    ec = self.epsdates[f.issuerTradingSymbol]
                    self.calendar.main(key, f, ec)
                    rlsdIssuers.add((f.issuerTradingSymbol, ec))
                else:
                    nullIssuers.add(f.issuerTradingSymbol)

        print nullIssuers

        # make currently available & Unavailable html
        availability = """<h4 style="font-family:tahoma,arial,sans-serif">EPS Calendar Summary</h4>"""
        availability += "<br><b><u>Currently Available EPS Issuers</u></b></br>"
        for pair in rlsdIssuers:
            availability += AvlTemp % (pair[0], pair[1].date, pair[1].period)

        availability += "<br></br>"

        availability += "<br><b><u>Currently Unavailable EPS Issuers</u></b></br>"
        for symbol in nullIssuers:
            availability += notAvlTemp % symbol

        return availability

    def filter(self):
        """
        Fine granular filter & html formatter.
        pass coarse filtered forms to checker, used result for formatter
        """
        # checker
        html = "EPS 1 Strategy: Matched Transaction Summary From " + \
            str(self.begDate) + " To " + str(self.now) + "<br>"
        html += """<br>Notation of day class</br>"""
        html += """<br>-1: after</br>"""
        html += """<br>0: 0~15 days</br>"""
        html += """<br>1: 16~30 days</br>"""
        html += """<br>2: 31~45 days</br>"""
        html += """<br>3: 46~60 days</br>"""
        html += """<br>4: 61~75 days</br>"""
        html += """<br>5: 76~90 days</br>"""
        html += """<h4 style="font-family:tahoma,arial,sans-serif">Buy EPS Summary</h4>"""

        for key, forms in self.formsbuyDict['forms'].items():
            self.formsbuyDict['forms'][key], self.formsbuyDict[
                'dayclass'][key] = self.checker.run(key, forms)

            # make format
            print key
            html += self.former.make(key,
                                     self.formsbuyDict['forms'][key],
                                     self.formsbuyDict['dayclass'][key])

        html += """<h4 style="font-family:tahoma,arial,sans-serif">Sell EPS Summary</h4>"""

        for key, forms in self.formssellDict['forms'].items():
            self.formssellDict['forms'][key], self.formssellDict[
                'dayclass'][key] = self.checker.run(key, forms)
            # make format
            print key
            html += self.former.make(key,
                                     self.formssellDict['forms'][key],
                                     self.formssellDict['dayclass'][key])

        return html

    @catcher
    def roughFilter(self):
        """
        Intuition is that eps strategy is very selective, so even a rough filter could
        greatly reduce the time needed for finer granularity filters.
        """
        # Roughly query for filtering
        # Group Buy
        self.formsbuyDict['forms']['GB'] = self.db.session.query(form).filter(form.acceptedDate > self.begDate, form.GT >= 3,
                                                                              or_(
                                                                                  form.transactionCode == 'BUY',
                                                                                  form.transactionCode == '10b5-1-BUY',
                                                                                  form.transactionCode == 'EX-B'),
                                                                              form.dollarValue > 90000, or_(form.investorType == 1, form.investorType == 2,
                                                                                                            form.investorType == 3)).order_by(form.dollarValue.desc()).all()
        print "Group Buy COMPLETE"
        # Last Buy
        self.formsbuyDict['forms']['LB'] = self.db.session.query(form).filter(form.acceptedDate > self.begDate,
                                                                              or_(
                                                                                  form.transactionCode == 'BUY',
                                                                                  form.transactionCode == '10b5-1-BUY',
                                                                                  form.transactionCode == 'EX-B'),
                                                                              form.form_id == additioninfo.form_id, additioninfo.lastbuy > 360, form.dollarValue > 90000).order_by(form.dollarValue.desc()).all()
        print "Last Buy COMPLETE"
        # First Buy
        self.formsbuyDict['forms']['FB'] = self.db.session.query(form).filter(form.acceptedDate > self.begDate,
                                                                              or_(
                                                                                  form.transactionCode == 'BUY',
                                                                                  form.transactionCode == '10b5-1-BUY',
                                                                                  form.transactionCode == 'EX-B'),
                                                                              form.form_id == additioninfo.form_id, additioninfo.lastbuy == -
                                                                              1, form.dollarValue > 90000,
                                                                              or_(form.investorType == 1, form.investorType == 2, form.investorType == 3)).order_by(form.dollarValue.desc()).all()
        print "First Buy COMPLETE"
        # BR Buy
        self.formsbuyDict['forms']['BR'] = self.db.session.query(form).filter(form.acceptedDate > self.begDate,
                                                                              or_(
                                                                                  form.transactionCode == 'BUY',
                                                                                  form.transactionCode == '10b5-1-BUY',
                                                                                  form.transactionCode == 'EX-B'),
                                                                              form.reversal > 180, form.dollarValue > 50000).order_by(form.dollarValue.desc()).all()
        print "Buy Reversal COMPLETE"
        # WA Buy
        # rough_tmp = self.db.session.query(tmpResults.form_id).filter(tmpResults.acceptedDate > self.begDate, tmpResults.return3MonthWA > 0.1, tmpResults.win3Month > 0.8,
        # and_(2 <= tmpResults.n3Month, tmpResults.n3Month <= 8)).all()
        self.formsbuyDict['forms']['WA'] = self.db.session.query(form, tmpResults). filter(form.acceptedDate > self.begDate, tmpResults.acceptedDate > self.begDate,
                                                                                           form.dollarValue > 90000, tmpResults.return3MonthWA > 0.1,
                                                                                           tmpResults.win3Month > 0.8,
                                                                                           or_(
                                                                                               tmpResults.transactionCode == 'BUY',
                                                                                               tmpResults.transactionCode == '10b5-1-BUY',
                                                                                               tmpResults.transactionCode == 'EX-B'),
                                                                                           and_(
                                                                                               2 <= tmpResults.n3Month, tmpResults.n3Month <= 8),
                                                                                           form.form_id == tmpResults.form_id).order_by(form.dollarValue.desc()).all()
        print "WA Buy COMPLETE"
        # BR Sell
        self.formssellDict['forms']['SR'] = self.db.session.query(form).filter(form.acceptedDate > self.begDate,
                                                                               or_(
                                                                                   form.transactionCode == 'SELL',
                                                                                   form.transactionCode == 'SELL*',
                                                                                   form.transactionCode == 'EX-S'),
                                                                               form.reversal < -180, form.dollarValue > 50000).order_by(form.dollarValue.desc()).all()
        print "Sell Reversal COMPLETE"
        # WA Sell
        # rough_tmp = self.db.session.query(tmpResults.form_id).filter(tmpResults.acceptedDate > self.begDate, tmpResults.return3MonthWA > 0.15, tmpResults.win3Month > 0.8,
        # and_(3 <= tmpResults.n3Month, tmpResults.n3Month <= 7)).all()
        self.formssellDict['forms']['WAS'] = self.db.session.query(form, tmpResults). filter(form.acceptedDate > self.begDate, tmpResults.acceptedDate > self.begDate,
                                                                                             form.dollarValue > 90000, tmpResults.return3MonthWA > 0.15,
                                                                                             tmpResults.win3Month > 0.8,
                                                                                             or_(
                                                                                                 tmpResults.transactionCode == 'SELL',
                                                                                                 tmpResults.transactionCode == 'SELL*',
                                                                                                 tmpResults.transactionCode == 'EX-S'),
                                                                                             and_(
                                                                                                 3 <= tmpResults.n3Month, tmpResults.n3Month <= 7),
                                                                                             form.form_id == tmpResults.form_id).order_by(form.dollarValue.desc()).all()
        print "WA Sell COMPLETE"

        return


if __name__ == "__main__":
    db = database(database.east)
    idlist = [
        '0000001750-05-000058-0',
        '0000001750-06-000020-0',
        '0000001750-07-000010-0',
        '0000001750-07-000019-0',
        '0000001750-08-000019-0',
        '0000001750-08-000024-0',
        '0000001750-08-000060-0',
        '0000001750-08-000062-0',
        '0000001750-08-000064-0',
        '0000001750-08-000066-0',
        '0000001750-08-000068-0',
        '0000001750-08-000069-0',
        '0000002230-15-000059-0',
        '0000002230-15-000063-0',
        '0000002230-15-000064-0',
        '0000002230-15-000065-0',
        '0000002488-05-000004-0',
        '0000002488-05-000008-0',
        '0000002488-05-000012-0',
        '0000002488-06-000006-0']
    forms = db.session.query(form).filter(form.form_id.in_(idlist)).all()
    #forms = db.session.query(form).filter(form.acceptedDate > '2013-12-31', form.acceptedDate < '2015-01-01').all()
    print "EPS TEST START"
    start = time.time()
    print "STEP 1: TEST GETDAYCLASS"
    checker = epsCriteria()
    for f in forms:
        print f.form_id, checker.getDayClassBuy(f)
        print f.form_id, checker.getDayClassSell(f)
    print "STEP 2: TEST FILTER"
    epsfilter = epsFilter()
    epsfilter.run()
    print "COMPLETE"
    print time.time() - start
