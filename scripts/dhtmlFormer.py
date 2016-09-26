import sys;
import os;
import time
import mysql.connector;
import datetime;
from mail import sendadvancedemail;
import yahoo_finance
from dtextAnalysis1 import item4Parser

class dhtmlFormmaker():
    """create the html file to send email"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.roundlist = ["return", "win", "alpha"]
        self.url = 'http://ec2-54-173-27-219.compute-1.amazonaws.com/lmg_app//search/?numofrows=50&';        
        self.issuerTemp = """<tr>
                <td class="filelink" style="font-size:10px;background-color:#FFFF99;text-align:center"><a
                    href="%(filelink)s" target="_parent">link</a></td>
                <td class="subjectName" style="font-size:10px;background-color:#FFFF99;text-align:center">%(subjectName)s</td>
                <td class="subjectCik" style="font-size:10px;background-color:#FFFF99;text-align:center">%(subjectCik)s</td>
                <td class="subjectCik" style="font-size:10px;background-color:#FFFF99;text-align:center"><a href="%(urlsubjectsymbol)s" target="_parent">%(subjectSymbol)s</a> </td>
                <td class="acceptedDate" style="font-size:10px;background-color:#FFFF99;text-align:center">%(acceptedDate)s</td>
                <td class="acceptedTime" style="font-size:10px;background-color:#FFFF99;text-align:center">%(acceptedTime)s</td>
                <td class="filedDate" style="font-size:10px;background-color:#FFFF99;text-align:center">%(filedDate)s</td>
                <td class="CUSIP" style="font-size:10px;background-color:#FFFF99;text-align:center">%(CUSIP)s</td>
                <td class="source" style="font-size:10px;background-color:#FFFF99;text-align:center">%(source)s</td>
                <td class="aggregateAmount" style="font-size:10px;background-color:#FFFF99;text-align:center">%(aggregateAmount)s</td>
                <td class="percent" style="font-size:10px;background-color:#FFFF99;text-align:center">%(percent)s</td>
                <td class="market" style="font-size:10px;background-color:#FFFF99;text-align:center">%(market_cap)s</td>
                </tr>"""

    #----------------------------------------------------------------------


    def body(self,forms):
        """"""
        htmlbody=''.join([self.issuerTemp % {"filelink":f[19],"subjectName":f[6], "subjectCik":f[5], "subjectSymbol":f[7],
                                  "urlsubjectsymbol":self.url+"tickername="+f[7], "acceptedDate":f[1],
                                  "acceptedTime":f[2], "filedDate":f[3], "CUSIP":f[11], "market_cap":f[20],
                                  "source":f[15], "aggregateAmount":"{:,d}".format(int(f[16])), "percent":f[17]}
                         for f in forms]);
        
        htmlbody+="""
            </tbody>
        </table>
        """        
        return htmlbody;    
            
# ---------------------------------------
    def createTitle(self, colNames):
        title = """ <table id="table"  class="tablesorter cruises scrollable custom-popup" style="width:100% "><thead><tr>"""
        temp = """<th class="%(item1)s" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" > <div>%(item2)s</div></th>"""
        title += ''.join([temp % {"item1":item, "item2":item if item != 'stats' else ' '} for item in colNames])
        title +=  "</tr></thead>"
        return title


    def makeStart(self, f):

        # Stock brief info & links
        htmlStart = """\
    <body>
    <p>
    IssuerTradingSymbol : <a href="http://ec2-54-173-27-219.compute-1.amazonaws.com/lmg_app//search/?numofrows=50&tickername=%(issuerTradingSymbol)s">%(issuerTradingSymbol)s   <br/>
    <a href="https://www.google.com/finance?q=%(issuerTradingSymbol)s" target="_blank">Google</a>|
    <a href="http://finance.yahoo.com/q?s=%(issuerTradingSymbol)s" target="_blank">Yahoo</a>|
    <a href="http://www.insiderinsights.com/free/index.php?s=ticker&o=-1&q=%(issuerTradingSymbol)s" target="_blank">InsiderInsights</a> |
    <a href="http://www.gurufocus.com/insider/%(issuerTradingSymbol)s" target="_blank">Guru</a> | 
    <a href="http://www.j3sg.com/Reports/Stock-Insider/Generate.php?DV=yes&tickerLookUp=%(issuerTradingSymbol)s" target="_blank">j3sg</a> |
    <a href="http://www.nasdaq.com/symbol/%(issuerTradingSymbol)s/short-interest" target="_blank">Short Interest</a> |
    <a href="http://whalewisdom.com/stock/%(issuerTradingSymbol)s" target="_blank">Whale Wisdom</a>
    </p>
    <p>
        SIC : %(sic)s <br>
        Filer Name: %(iname)s <br>
        Filer Cik: %(icik)s <br>
        <!--Filer Symbol : %(filedSymbol)s <br>-->
    </p>
	"""
        htmlStart = htmlStart%{"issuerTradingSymbol":f[7], "sic":f[13], "iname":f[9], "icik":f[8], "filedSymbol":f[10]}
    
        html = ""
        #html += """<br>Category of Source</br>"""
        #html += """<br>SC: Subject Company (Company whose securities are being acquired)</br>"""
        #html += """<br>BK: Bank</br>"""
        #html += """<br>AF: Affiliate (of reporting person)</br>"""
        #html += """<br>WC: Working Capital (of reporting person)</br>"""
        #html += """<br>PF: Personal Funds (of reporting person)</br>"""
        #html += """<br>OO: Other</br>"""
        #html += """<br>NA: Not available</br>"""

        htmlStart = html + htmlStart
        return htmlStart


    def optimizationStrategyInfo(self,f):
        global optimizationFlag
        optimizationFlag = 0
        #print(optimizationFlag)
        yahoo = yahoo_finance.Share(f[7])
        yahoo.refresh()
        price = yahoo.get_price()
        if price is None:
            aggregateDollarValue = 'NA'
        else:
            aggregateDollarValue=int(f[16])*float(price)/1000000
        mktcap=f[20]
        percentChange=float(f[17])
        if mktcap != 'NA':
            if mktcap.endswith('M'):
                mktcap=float(mktcap[:-1])
            elif mktcap.endswith('B'):
                mktcap=float(mktcap[:-1])*1000
            else:
                mktcap=float(mktcap)/1000
        mktcapRange=[100,250,500,1000,float('inf')]
        dollarValueRange=[0,20,50,150,float('inf')]
        percentChangeRange=[4,6,10,100]

        #print(mktcap)
        index=0
        mktcapFlag=0
        while(mktcap>=mktcapRange[index] and mktcap!='NA'):
            index+=1
            mktcapFlag=index

        index=0
        dollarValueFlag=0
        while(aggregateDollarValue>=dollarValueRange[index] and aggregateDollarValue!='NA'):
            index+=1
            dollarValueFlag=index

        index=0
        percentChangeFlag=0
        while(percentChange>=percentChangeRange[index]):
            index+=1
            percentChangeFlag=index
        
        strategyNo=str(percentChangeFlag)+str(mktcapFlag)+str(dollarValueFlag)
        strategylist=['222','211','233','132','121','243','244','143','144','312']
        if strategyNo in strategylist:
            strategyID=strategylist.index(strategyNo)+1
        else:
            strategyID=-1

        if strategyID!=-1:
            for i in range(5):
                try:
                    cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
                        password= 'yangfan19931001', database='fan_new')
                    cursor = cnx.cursor()
                    select_row = ("SELECT * FROM 13D_Optimization_Strategy_List where StrategyId = %s" % (str(strategyID)))
                    cursor.execute(select_row)
                    data = cursor.fetchall()
                    form = list(data)
                    #print(forms)
                    #htmlbody+=self.inserthtmlform(forms);
                    #print(htmlbody)
                    cursor.close()
                    cnx.close()
                    break;
                except mysql.connector.Error as err:
                    sendadvancedemail("13D Summary bug is", str(err.msg), "")
                    time.sleep(10)
                    continue
            htmlStrategyInfo = """\
            <p><u><b>Optimization Strategy Criteria Info</b></u>
            <br>Close Price > $1; From 2005.1-2015.5; Market_Cap > $100m; Dollar Volume > $0.5m; Only Common Stocks; No IPO/Acquisition; Slippage 0.5&#37;
            <br>
            <br><b>Strategy No. : %s </b> <br>Percent : %s <br>Dollar Value($m) : %s <br>Market_Cap($m) : %s <br>Sample Size: %s 
            """ % (str(strategyID),form[0][1],form[0][2],form[0][3],form[0][4])
            
            optimizationFlag = 1
            htmlStrategyInfo+=self.optimizationStrategyHist(form)


        else:
            optimizationFlag = 0
            htmlStrategyInfo = " "
            #htmlStrategyInfo = """\
            #<p><u><b>Optimization Strategy Criteria Info</b></u>
            #<br>Close Price > $1; From 2005.1-2015.5; Market_Cap > $100m; Dollar Volume > $0.5m; Only Common Stocks; No IPO/Acquisition; Slippage 0.5&#37;
            #<br>
            #<br>Strategy No. :  <br>Percent :  <br>Dollar Value($m) :  <br>Market_Cap($m) :  <br>Sample Size:
            #""" 
            htmlStrategyInfo+=self.optimizationStrategyHist([])
        print("optimization")
	return htmlStrategyInfo


    def textAnalysisStrategyInfo(self,f):
        global textAnalysisFlag1
        global textAnalysisFlag2
        global textAnalysisFlag3
        textAnalysisFlag1 = 0
        textAnalysisFlag2 = 0
        textAnalysisFlag3 = 0
        #print(textAnalysisFlag3)
       
        strategyDict=item4Parser(f)
        #print(strategyDict)
        strategyList_1word=strategyDict['1word']
        strategyList_2word=strategyDict['2word']
        strategyList_3word=strategyDict['3word']
        htmlStrategyInfo="""\
                <p><u><b>Text Analysis Strategy Criteria Info</b></u>
                <br>Close Price > $1; From 2005.1-2015.5; Market_Cap > $100m; Dollar Volume > $0.5m; Only Common Stocks; No IPO/Acquisition; Slippage 0.5&#37;
                <br>"""
        #print(strategyList_1word)
        #print(strategyList_2word)
        #print(strategyList_3word)
        if len(strategyList_1word)>0:
            for strategyID in strategyList_1word:
                for i in range(5):
                    try:
                        cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
                            password= 'yangfan19931001', database='fan_new')
                        cursor = cnx.cursor()
                        select_row = ("SELECT * FROM fan_new.13D_1word where StrategyId = %s" % (str(strategyID)))
                        cursor.execute(select_row)
                        data = cursor.fetchall()
                        form = list(data)
                        #print(forms)
                        #htmlbody+=self.inserthtmlform(forms);
                        #print(htmlbody)
                        cursor.close()
                        cnx.close()
                        break;
                    except mysql.connector.Error as err:
                        sendadvancedemail("13D Summary bug is", str(err.msg), "")
                        time.sleep(10)
                        continue
                htmlStrategyInfo+= """
                <br><b>1 Word Strategy No. : %s </b> <br>Keywords : %s <br>Sample Size: %s
                """ % (str(strategyID),form[0][1],form[0][2])
                htmlStrategyInfo+=self.textAnalysisStrategyHist(form)
            
            textAnalysisFlag1 = 1

        elif len(strategyList_2word)>0:
            for strategyID in strategyList_2word:
                for i in range(5):
                    try:
                        cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
                            password= 'yangfan19931001', database='fan_new')
                        cursor = cnx.cursor()
                        select_row = ("SELECT * FROM fan_new.13D_2word where StrategyId = %s" % (str(strategyID)))
                        cursor.execute(select_row)
                        data = cursor.fetchall()
                        form = list(data)
                        #print(forms)
                        #htmlbody+=self.inserthtmlform(forms);
                        #print(htmlbody)
                        cursor.close()
                        cnx.close()
                        break;
                    except mysql.connector.Error as err:
                        sendadvancedemail("13D Summary bug is", str(err.msg), "")
                        time.sleep(10)
                        continue
                htmlStrategyInfo+= """
                <br><b>2 Word Strategy No. : %s </b> <br>Keywords : %s <br>Sample Size: %s
                """ % (str(strategyID),form[0][1]+"&"+form[0][2],form[0][3])
                htmlStrategyInfo+=self.textAnalysisStrategyHist(form)
            textAnalysisFlag2 = 1

        elif len(strategyList_3word)>0:
            for strategyID in strategyList_3word:
                for i in range(5):
                    try:
                        cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
                            password= 'yangfan19931001', database='fan_new')
                        cursor = cnx.cursor()
                        select_row = ("SELECT * FROM fan_new.13D_3word where StrategyId = %s" % (str(strategyID)))
                        cursor.execute(select_row)
                        data = cursor.fetchall()
                        form = list(data)
                        #print(forms)
                        #htmlbody+=self.inserthtmlform(forms);
                        #print(htmlbody)
                        cursor.close()
                        cnx.close()
                        break;
                    except mysql.connector.Error as err:
                        sendadvancedemail("13D Summary bug is", str(err.msg), "")
                        time.sleep(10)
                        continue
                htmlStrategyInfo+= """
                <br><b>3 Word Strategy No. : %s </b> <br>Keywords : %s <br>Sample Size: %s
                """ % (str(strategyID),form[0][1]+"&"+form[0][2]+"&"+form[0][3],form[0][4])
                htmlStrategyInfo+=self.textAnalysisStrategyHist(form)
            textAnalysisFlag3 = 1



        else:

            htmlStrategyInfo = " "
            #htmlStrategyInfo = """\
            #<p><u><b>Text Analysis Strategy Criteria Info</b></u>
            #<br>Close Price > $1; From 2005.1-2015.5; Market_Cap > $100m; Dollar Volume > $0.5m; Only Common Stocks; No IPO/Acquisition; Slippage 0.5&#37;
            #<br>
            #<br>Strategy No. :   <br>Keywords :  <br>Sample Size:
            #"""
            #htmlStrategyInfo+=self.textAnalysisStrategyHist([])
        print("test") 

	return htmlStrategyInfo




    def makeRptOwnerHist(self):
        htmltitle = "<p><b><u>Filed Company Historical Performance</u></b></p>"
        htmltitle += self.createTitle(["stats","1Day", "1week", "2week" ,"3week", "1Month", "2Month", "3Month", "6Month", "1Year"])

        htmlIHistory = """\
            <tr>
             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:left;">return WA</td>
            </tr>
            <tr>
             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:left;">alpha</td>
            </tr>
            <tr>
             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:left;">win</td>
            </tr>
            <tr>
             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:left;">n</td>
            </tr>
            </tbody>
         </table>
        </p>
        """ 
        return htmltitle + htmlIHistory
    
    def optimizationStrategyHist(self,f):
        htmltitle = "<p><b><u>Optimization Strategy Historical Performance</u></b><br>"
        htmltitle += self.createTitle(["stats","1Day", "3Day","1week", "2week" ,"3week", "1Month"])
        if len(f)>0: 
            #print(f)
            f=f[0]
            htmlStrategyHist = """
                <tr>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">Sharpe Ratio</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                </tr>
                <tr>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">Return(&#37;)</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                 <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
                </tr>
                </tbody>
              </table>
            </p>
            """ %(f[5],f[6],f[7],f[8],f[9],f[10],f[11]*100,f[12]*100,f[13]*100,f[14]*100,f[15]*100,f[16]*100)
            return htmltitle + htmlStrategyHist
        else:
            htmlStrategyHist = " "
            #htmlStrategyHist = """
            #    <tr>
            #     <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">Sharpe Ratio</td>
            #    </tr>
            #    <tr>
            #     <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">return(&#37;)</td>
            #    </tr>
            #    </tbody>
            #  </table>
            #</p>
            #"""

            return  htmlStrategyHist


    def textAnalysisStrategyHist(self,f):
        htmltitle = "<p><b><u>Text Analysis Strategy Historical Performance</u></b><br>"
        htmltitle += self.createTitle(["stats","1week", "2week" ,"3week", "1Month"])
        htmlStrategyHist = ""
        if len(f)>0: 
            #print(f)
            f=f[0]
            #print(f)
            #print(len(f))
            if len(f)==11:
                output=(f[3],f[4],f[5],f[6],f[7]*100,f[8]*100,f[9]*100,f[10]*100)
            elif len(f)==12:
                output=(f[4],f[5],f[6],f[7],f[8]*100,f[9]*100,f[10]*100,f[11]*100)
            elif len(f)==13:
                output=(f[5],f[6],f[7],f[8],f[9]*100,f[10]*100,f[11]*100,f[12]*100)

            #print(output)

            htmlStrategyHist += """
	            <tr>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">Sharpe Ratio</td>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>

	            </tr>
	            <tr>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">Return(&#37;)</td>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">%.2f</td>

	            </tr>
	            </tbody>
	          </table>
	        </p>
	        """ % output
        else:
	        htmlStrategyHist += """
	            <tr>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">Sharpe Ratio</td>
	            </tr>
	            <tr>
	             <td class="stat" style="font-size:10px;background-color:#FFFFFF;text-align:center;">return(&#37;)</td>
	            </tr>
	            </tbody>
	          </table>
	        </p>
	        """

        return htmltitle + htmlStrategyHist

    #----------------------------------------------------------------------
    def getheader(self):
        """"""
        htmlheader="";        
        return htmlheader;

    #----------------------------------------------------------------------
    def inserthtmlform(self,forms):
        """"""
        htmlformtitle="""
        <table id="table"  class="tablesorter cruises scrollable custom-popup" style="width:100% "><thead><tr><th data-priority="critical"class="filelink" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" valign="bottom">File Link</th>
        <th class="filername" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" valign="bottom"><div>Filer Name</div></th>
        <th class="filercik" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" valign="bottom"><div>Filer Cik</div></th>
        <th class="filersymbol" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" valign="bottom"><div>Filer Symbol</div></th>
        <th class="subjectname" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" valign="bottom"><div>Subject Name</div></th>
        <th class="subjectcik" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" valign="bottom"><div>Subject Cik</div></th>
        <th class="subjectsymbol" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" valign="bottom"><div>Subject Symbol</div></th>
        <th class="accepteddate"  style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" ><div>Accpeted Date</div></th>
        <th class="acceptedtime" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" ><div>Time</div></th>
        <th class="fileddate" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" ><div>Filed Date</div></th>
        <th class="cusip" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" ><div>CUSIP</div></th>
        <th class="source" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" ><div>Source</div></th>
        <th class="industry" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" ><div>Industry</div></th>
        <th class="amount" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" > <div>Aggregate Amount</div></th>
        <th class="percent" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" ><div>Percent</div></th>
        <th class="market" style="font-weight:bold;font-size:11px;font-family:arial,sans-serif;background-color:silver;border-right:1px solid black;border-bottom:2px solid black" ><div>Market_cap</div></th>
</tr></thead>""";
        htmlform="<tbody>";
        for idx,f in enumerate(forms):
            temp = self.url+"tickername="+f[7]
            if idx%2==0:
                htmlform+="""
                <tr >
                <td class="filelink" style="font-size:10px;text-align:center"><a
                     href="%s" target="_parent">link</a></td>
                <td class="filername" style="font-size:10px;text-align:center">%s</td>
                <td class="filercik" style="font-size:10px;text-align:center">%s</td>
                <td class="filersymbol" style="font-size:10px;text-align:center">%s</td>
                <td class="subjectname" style="font-size:10px;text-align:center">%s</td>
                <td class="subjectcik" style="font-size:10px;text-align:center">%s</td>
                <td class="subjectsymbol" style="font-size:10px;text-align:center"><a href="%s" target="_parent">%s</a></td>
                <td class="accepteddate" style="font-size:10px;text-align:center">%s</td>
                <td class="acceptedtime" style="font-size:10px;text-align:center">%s</td>
                <td class="fileddate" style="font-size:10px;text-align:center">%s</td>
                <td class="cusip" style="font-size:10px;text-align:center">%s</td>
                <td class="source" style="font-size:10px;text-align:center">%s</td>
                <td class="industry" style="font-size:10px;text-align:center">%s</td>
                <td class="amount" style="font-size:10px;text-align:center">%s</td>
                <td class="percent" style="font-size:10px;text-align:center">%s</td>
                <td class="market" style="font-size:10px;text-align:center">%s</td>
                </tr>
                """ % (f[19], f[9], f[8], f[10], f[6], f[5], temp, f[7], f[1], f[2], f[3], f[11], f[15], f[13], "{:,d}".format(int(f[16])), f[17], f[20]);
            else:
                htmlform+="""
                <tr >
                <td class="filelink" style="font-size:10px;background-color:#FFFF99;text-align:center"><a
                     href="%s" target="_parent">link</a></td>
                <td class="filername" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="filercik" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="filersymbol" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="subjectname" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="subjectcik" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="subjectsymbol" style="font-size:10px;background-color:#FFFF99;text-align:center"><a href="%s" target="_parent">%s</a></td>
                <td class="accepteddate" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="acceptedtime" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="fileddate" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="cusip" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="source" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="industry" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="amount" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="percent" style="font-size:10px;background-color:#FFFF99;text-align:center">%s</td>
                <td class="market" style="font-size:10px;backgroung-color:#FFFF99;text-align:center">%s</td>
                </tr>
                """ % (f[19], f[9], f[8], f[10], f[6], f[5], temp, f[7], f[1], f[2], f[3], f[11], f[15], f[13], "{:,d}".format(int(f[16])), f[17], f[20]);    
        htmlform+="""
        </tbody>
</table>
        """
        htmlform=htmlformtitle+htmlform;
        htmlform=htmlform.replace("\n", "");
        htmlform=htmlform.replace("\t", "");
        return (htmlform);    


    #----------------------------------------------------------------------
    def slpFormat(self, v):
        return str(int((float(v) * 10000.)))+'bps'

    def pctFormat(self, v):
        return "{:,.2f}".format(float(v)*100.) + '%'

    def sharpeFormat(self, s):
            # possible bug in s > 0., the comparison of float
            if s > 0.:
                    return "{:,.1f}".format(s)+'x'
            else:
                    return '('+"{:,.1f}".format(-s)+'x'+')'

    def amountFormat(self, num):
        return "{:,d}".format(int(num))
    
    #----------------------------------------------------------------------
    def makeTransactionSum(self):

        date = datetime.date.today()
        #date=datetime.date(2016,8,29)
        date = """'""" +str(date.year) + '-' + str(date.month) + '-' + str(date.day) + """'"""

        htmlbody = """<h4 style="font-family:tahoma,arial,sans-serif">Category of Source</h4>"""
        htmlbody += """<br>SC: Subject Company (Company whose securities are being acquired)</br>"""
        htmlbody += """<br>BK: Bank</br>"""
        htmlbody += """<br>AF: Affiliate (of reporting person)</br>"""
        htmlbody += """<br>WC: Working Capital (of reporting person)</br>"""
        htmlbody += """<br>PF: Personal Funds (of reporting person)</br>"""
        htmlbody += """<br>OO: Other</br>"""
        htmlbody += """<br>NA: Not available</br>"""
        
        htmlbody+="""<body> 
        <br>

          <div id="data"  class="scrollableContainer">
          <h4 style="font-family:tahoma,arial,sans-serif">13D Transaction Summary</h4>
          """;

        for i in range(5):
            try:
                cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
                    password= 'yangfan19931001', database='SC13D')
                cursor = cnx.cursor()
                select_column = ("""SELECT * FROM 13D_form_new2 where fileDate = %s ORDER BY acceptedDate, acceptedTime LIMIT 10""")
                cursor.execute(select_column % (date))
                data = cursor.fetchall()
                forms = list(data)
                #print(forms)
                #htmlbody+=self.inserthtmlform(forms);
                #print(htmlbody)
                cursor.close()
                cnx.close()
                break;
            except mysql.connector.Error as err:
                sendadvancedemail("13D Summary bug is", str(err.msg), "")
                time.sleep(10)
                continue

        htmlbody+=self.inserthtmlform(forms)
        htmlbody+="""
           </div>
 </div>

</body>
</html>
        """;
        return htmlbody
        
    def makeStrategy(self,f):
        return self.optimizationStrategyInfo(f) + self.textAnalysisStrategyInfo(f)
        
    def makeforms(self, f):
        html = ""
        forms = None
        for i in range(5):
            try:
                cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', 
                    password= 'yangfan19931001', database='SC13D')
                cursor = cnx.cursor()
                select_column = ("""SELECT * FROM 13D_form_new2 where filedCik = %(cik)s ORDER BY acceptedDate DESC, acceptedTime DESC LIMIT 10""")
                cursor.execute(select_column % {"cik":f[8]})
                data = cursor.fetchall()
                forms = list(data)
                #print(forms)
                #colnames = ["File Link", "Suject Name", "Subject Cik", "Symbol", "Accepted Date", "Time", "Filed Date", "CUSIP", "Source", "Aggregate Amount", "Percent"]
                #html = "<p><b><u>Filed Company History</b></u></p>"+self.createTitle(colnames)+self.body(forms);
                cursor.close()
                cnx.close()
                break;
            except mysql.connector.Error as err:
                sendadvancedemail("13D Parser bug", str(err.msg), "")
                time.sleep(10)
                continue
        #sendadvancedemail("The html generating is right", "point0", "")
        colnames = ["File Link", "Subject Name", "Subject Cik", "Symbol", "Accepted Date", "Time", "Filed Date", "CUSIP", "Source", "Aggregate Amount", "Percent", "Market_cap"]
        if forms:
            html = "<p><b><u>Filed Company History</b></u></p>" + self.createTitle(colnames)+self.body(forms);
        else:
            html = "<p><b><u>Filed Company History</b></u></p>" + self.createTitle(colnames)
        #sendadvancedemail("The html generating is right", "point1", html)
        return html;

    def makeWA(self, f):
        html = self.makeStart(f)
        #print("start is done")
        html += self.makeforms(f)
        #print("forms is done")
        html += self.makeStrategy(f)
        print("strategy is done")
        html += """<br>Category of Source</br>"""
        html += """<br>SC: Subject Company (Company whose securities are being acquired)</br>"""
        html += """<br>BK: Bank</br>"""
        html += """<br>AF: Affiliate (of reporting person)</br>"""
        html += """<br>WC: Working Capital (of reporting person)</br>"""
        html += """<br>PF: Personal Funds (of reporting person)</br>"""
        html += """<br>OO: Other</br>"""
        html += """<br>NA: Not available</br>"""
        #html += self.makeRptOwnerHist()
        #sendadvancedemail("The html generating is right", "point2", html)
        #html += self.makeforms(f)
        return html,optimizationFlag,textAnalysisFlag1,textAnalysisFlag2,textAnalysisFlag3

if __name__ == "__main__":
    maker = dhtmlFormmaker()
    html = maker.makeTransactionSum()
    date = datetime.date.today()
    #date=datetime.date(2016,8,29)
    sendadvancedemail("*13D Transaction Summary %s" % (date),"Transaction Summary", html);

