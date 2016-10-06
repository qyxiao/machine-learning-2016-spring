import pandas as pd
import urllib2 as ur
import nltk 
from nltk.probability import FreqDist
import html2text
import re
import numpy as np
import mysql.connector

def item4Parser(f):
	link=f[19]
	data=ur.urlopen(link).read()
	data=str(data)
	if link[-3:]=='htm':
		data=html2text.html2text(data).replace('\\n','')
	startloc=data.find('Purpose of the Transaction')
	endloc=data.find('Interest in Securities')
	if startloc==-1:
		startloc=data.find('Purpose of Transaction')		
	if startloc==-1:
		startloc=data.find('Purposes of Transactions')
	if startloc==-1:
		startloc=data.find('Purposes ofTransactions')
	if endloc==-1:
		endloc=data.find('Interest in Securities')
	if startloc==-1:
		startloc=data.find('Purpose Of Transaction')
	if endloc==-1:
		endloc=data.find('Interest In Securities')
	if startloc==-1:
		startloc=data.find('Purpose ofTransaction')
	if startloc==-1:
		startloc=data.find('PURPOSE OF TRANSACTION')
	if endloc==-1:
		endloc=data.find('INTEREST IN SECURITIES')
	if endloc==-1:
		endloc=data.find('INTERESTS IN THE SECURITIES')
	if startloc==-1:
		startloc=data.find('Purposeof Transaction')
	if startloc==-1:
		startloc=data.find('PURPOSE OF')
	if startloc==-1:
		startloc=data.find('Purpose of the')
	if startloc==-1:
		startloc=data.find('OF TRANSACTION')
	if startloc==-1:
		startloc=data.find('Item 4.')
	if startloc==-1:
		startloc=data.find('Purpose Of The Transaction')
	if startloc==-1:
		startloc=data.find('Purposes of the Transaction')
	if endloc==-1:
		endloc=data.find('Interestin Securities')
	if endloc==-1:
		endloc=data.find('Interest inSecurities')
	if endloc==-1:
		endloc=data.find('Interests in Securities')
	if endloc==-1:
		endloc=data.find('Interests in the Securities')
	if endloc==-1:
		endloc=data.find('Interests inSecurities')
	if endloc==-1:
		endloc=data.find('Interest in the Securities')
	if endloc==-1:
		endloc=data.find('IN SECURITIES OF')
	if endloc==-1:
		endloc=data.find('INTEREST IN')
	if endloc==-1:
		endloc=data.find('Interest in Common')
	if endloc==-1:
		endloc=data.find('Item 6.')
	if endloc==-1:
		endloc=data.find('Item 7.')


	print(startloc,endloc)
	if endloc!=-1 and startloc!=-1:
		item4=data[startloc:endloc]
		item4list=item4.split('\\n')
		item4text=' '.join(item4list)
		item4text=item4text.lower()

	strategyList=[]

	worddict={'wordlist1':['dispositions'],'wordlist2':['conversation'],'wordlist3':['increase shareholder value'],'wordlist4':['election'],'wordlist5':['strategic alternative'],
	'wordlist6':['attractive investment'],'wordlist7':['letter'],'wordlist8':['purchasing additional shares'],'wordlist9':['voted'],'wordlist10':['nominate'],
	'wordlist11':['tender'],'wordlist12':['with management'],'wordlist13':['chief executive officer'],'wordlist14':['strategy'],'wordlist15':['undervalued situation']}

	new_item4 = item4text.replace('\n',' ').lower()
	for i in range(1,16):
		dictName='wordlist'+str(i)
		if worddict[dictName][0] in new_item4:
			print("Item 4 Parsed type 1")
			strategyList.append(i)

	tokens = [] #nltk.word_tokenize(item4text)
	worddict={'wordlist16':['communicate','communication','communicated','communicating'],'wordlist17':['undervalued','attractive'],'wordlist18':['met','meet','meeting'],'wordlist19':['favorable','realize','profit','profits'],
	'wordlist20':['active'],'wordlist21':['benefit','benefits'],'wordlist22':['increase','increasing','increased','improve','improved','improving'],'wordlist23':['good','maximize','long-term'],
	'wordlist24':['strategy','strategic','strategies'],'wordlist25':['monitor'],'wordlist26':['designate'],'wordlist27':['facilitate']}
	
	for i in range(16,28):
		dictName='wordlist'+str(i)
		if (len([w for w in worddict[dictName] if w in tokens])>=1) and i!=22:
			print("Item 4 Parsed type 2")
			#print(i)
			#print([w for w in worddict[dictName] if w in tokens])
			strategyList.append(i)
		elif (len([w for w in worddict[dictName] if w in tokens])>=1) and ('value' in tokens or 'values' in tokens or 'profit' in tokens or 'profits' in tokens) and i==22:
			print("Item 4 Parsed type 3")
			#print(i)
			#print([w for w in worddict[dictName] if w in tokens])
			strategyList.append(i)

	strategyList_1word=strategyList

	strategyList=[]
	cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', password= 'yangfan19931001', database='fan_new')
	cursor = cnx.cursor()
	select_strat = "SELECT * FROM fan_new.13D_2word;"

	cursor.execute(select_strat)
	data = cursor.fetchall()
	data = list(data)
	for row in data:
		word1=row[1]
		word2=row[2]
		if word1 in new_item4 and word2 in new_item4:
			strategyList.append(row[0])

	strategyList_2word=strategyList

	strategyList=[]
	cnx = mysql.connector.connect(user='fanyang', host= 'edgar-2015-05-17.ciwfn1kzluad.us-east-1.rds.amazonaws.com', password= 'yangfan19931001', database='fan_new')
	cursor = cnx.cursor()
	select_strat = "SELECT * FROM fan_new.13D_3word;"

	cursor.execute(select_strat)
	data = cursor.fetchall()
	data = list(data)
	for row in data:
		word1=row[1]
		word2=row[2]
		word3=row[3]
		if word1 in new_item4 and word2 in new_item4 and word3 in new_item4:
			strategyList.append(row[0])

	strategyList_3word=strategyList	

	strategyDict={'1word':strategyList_1word,'2word':strategyList_2word,'3word':strategyList_3word}


	return strategyDict

	


