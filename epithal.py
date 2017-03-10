#!/usr/bin/python

# EPITHAL
# Main functions/workflow
# TODO? move some of this to eplib.py

import os
import json
import eveapi
import presetup
import eplib

cachetime_market = 600

eplib.loadnames()
#items=eplib.loaditems()

tradehubs=eplib.loadtradehubs()
products=[]
productcount=0

def findlowestsellpricewithquant(hub, typeid, quant):
	lowestprice = -1
	apistring="markets/"+str(hub["region_id"])+"/orders/?type_id="+str(typeid)
	orders_file=eveapi.pullfromcache(apistring,cachetime_market)
	with open(orders_file) as json_data:
		orders=json.load(json_data)
		for order in orders:
			if order["location_id"]==hub["station_id"] and order["is_buy_order"]==False:
				if lowestprice == -1 or order["price"] < lowestprice:
					lowestprice = order["price"]
	
	return lowestprice

def checksellorders():
#	typename=raw_input("Enter product to price-check: ")
#	typeid = -1
#	if len(typename) > 0:
#		typeid = eplib.gettypeid(typename)
	typeid = eplib.takenameinput("Enter product to price-check: ")
	if(typeid < 1):
		print "No matching item found."
	else:
		print
		for hub in tradehubs:
			price = findlowestsellpricewithquant(hub, typeid, 1)
			print hub["hubname"].rjust(20) + ": {:,.2f}".format(price)	

def loadproductindex():
	prodpath = os.path.join("ep_data","products")
	i=0
	if not os.path.exists(prodpath):
		print "No saved products found."
		return 0
	else:
		for file in os.listdir(prodpath):
			if file.lower().endswith('.json'):
				with open(os.path.join(prodpath,file)) as json_data:
					prodd=json.load(json_data)
					pi={}
					pi.setdefault("nickname",prodd["nickname"])
					pi.setdefault("filename",file)
					products.append(pi)
					i+=1
	
	return i
	
def showproductindex():
	i=1
	print
	for prod in products:
		print str(i) + ") " + prod["nickname"]
		i+=1
	
# defines a product as a set of input materials and output
def defineproduct():
	global productcount
	matarray = [0]*50000
	fillerlines = 0
	
	#step 1: take a list of meterials copy-pasted from the EvE industry interface
	#todo? expand to take manual material x quantity input
	
	print "Copy-paste input materials from the EvE industry interface."
	print "Type 'done' when finished."
	print
	iline=""
	while iline != 'done':
		iline=raw_input(">")
		fields = iline.rsplit(None,4)
		if len(fields) == 5:
			try:
				typeid=int(fields[4])
				quant=int(fields[1])
				matarray[typeid] += quant
			except ValueError:
				fillerlines += 1
	
	print
	print "Total material needs:"
	print
	
	#sum up materials and create a dict to hold them
	
	prodd = {}
	prodd["inputs"] = []
		
	i=0
	while i < len(matarray):
		if matarray[i]>0:
			inputmat = {}
			inputmat["typeid"]=i
			inputmat["quant"]=matarray[i]
			print str(matarray[i]).rjust(20) + " x " + eplib.getname(i)
			prodd["inputs"].append(inputmat)
		i+=1
		
	#step 2: define an output product
	
	print 
	validoutput = 0
	while validoutput == 0:
		typeid=eplib.takenameinput("Enter output product: ")
#		typeid = -1
#		if len(typename) > 0:
#			typeid = eplib.gettypeid(typename)
		if(typeid < 0):
			print "No such item found. Try again."
			validoutput = 0
		else:
			prodd.setdefault("outputid",typeid)
			validoutput = 1
			
	#step 3: defien an output quantity
			
	validoutcount = 0
	while validoutcount == 0:
		outcounts=raw_input("Enter output quantity: ")
		try:
			outcount=int(outcounts)
			if outcount < 1:
				print "Cannot produce a zero or negative number of product."
			else:
				prodd.setdefault("outputquant",outcount)
				validoutcount = 1
		except ValueError:
			print "Please enter an number."
			
	prodd.setdefault("outputname",eplib.getname(prodd["outputid"]))
	
	#finishing touches: get a meaningful (or not) nickname and save the dict as a json for later
			
	defaultnick = eplib.getname(prodd["outputid"]) + " x " + str(prodd["outputquant"])
	
	print "Enter product nickname, or press enter to accept default."
	print "("+defaultnick+")"
	
	nickname=raw_input("> ")
	if len(nickname) < 1:
		nickname = defaultnick
		
	prodd.setdefault("nickname",nickname)
	
	outpath = os.path.join("ep_data","products")
	if not os.path.exists(outpath):
		os.makedirs(outpath)
		
	filename = nickname.replace(" ","_").lower()+".json"
	filepath = os.path.join(outpath,filename)
	
	with open (filepath, 'w') as outfile:
		json.dump(prodd,outfile)
		outfile.close()
		print "Saved product "+ nickname

	#add it to the index
		
	prodi={}
	prodi.setdefault("nickname",nickname)
	prodi.setdefault("filename",filename)
	products.append(prodi)
	productcount+=1
		
def selecthub(prompt):
	i=1
	print
	for hub in tradehubs:
		print str(i) + ") "+hub["hubname"]
		i+=1
	print
	hubno=raw_input(prompt)
	try:
		if not int(hubno):
			raise ValueError()
	except ValueError:
		print "Please enter a number!"
	return int(hubno)-1
	
def prodreport(prod,buyhub,sellhub,short):
	buildprice = 0
	failedbuild = 0
	if short == False:
		print
		print "Running report on " + prod["nickname"] + "."
		print "Buying in " + buyhub["hubname"] + " selling in " + sellhub["hubname"] + "."
		print
	json_file=os.path.join("ep_data","products",prod["filename"])
	with open(json_file) as json_data:
		proddata=json.load(json_data)
#		print proddata
		for material in proddata["inputs"]:
			matprice = findlowestsellpricewithquant(buyhub,material["typeid"],material["quant"])
			if matprice < 0:
				if short==False:
					print "No suitable sell order for " + eplib.getname(material["typeid"]) + "!"
				failedbuild = 1
			elif short==False:
				print eplib.getname(material["typeid"]) + " selling for " + str(matprice)
			buildprice += (matprice * material["quant"])
			
		if short==False:
			print
			
		if failedbuild > 0:
			if short==True:
				print prod["nickname"].rjust(40) + " parts not for sale in " + buyhub["hubname"] + "!"
			else:
				print "One or more materials not for sale in sufficient quantity in "+buyhub["hubname"] + "!"
		else:
			sellprice = findlowestsellpricewithquant(sellhub,proddata["outputid"],1) * proddata["outputquant"]
			profit = sellprice-buildprice
			profitratio = profit/buildprice
			if short==True:
				print prod["nickname"].rjust(40) + "{:,.2f}".format(profit).rjust(20) + " ({:.0%})".format(profitratio)
			else:
				print "Total build price: {:,.2f}".format(buildprice)
				print "Selling for: {:,.2f}".format(sellprice)
				if profit > 0:
					print "Net profit: {:,.2f}".format(profit)
					print "Profit ratio: {:.0%}".format(profitratio)
				else:
					print "Net loss: {:,.2f}".format(profit)
					print "Loss ratio: {:.0%}".format(profitratio)
		
	
def marketanalysis():
	global productcount
	if(productcount>0):
		showproductindex()

		print
		prodno = raw_input("Run report on which product? (or 'all') ")
		try:
			if prodno=="a" or prodno=="all":
				buyhubi = selecthub("Select buy hub: ")
				sellhubi = selecthub("Select sell hub: ")
				print
				print "PRODUCT".rjust(40) + "GROSS PROFIT".rjust(20) + " RATIO"
				for product in products:
					prodreport(product,tradehubs[buyhubi],tradehubs[sellhubi],True)
			elif not int(prodno):
				raise ValueError()
			else:
				prodi=int(prodno)
				prodi-=1
				if prodi < 0:
					print "Please enter a valid product number."
				else:
					buyhubi = selecthub("Select buy hub: ")
					sellhubi = selecthub("Select sell hub: ")
					prodreport(products[prodi],tradehubs[buyhubi],tradehubs[sellhubi],False)
		except ValueError:
			print "Please enter a number!"
	else:
		print "You need to define at least one product first."

eplib.showlogo()
productcount=loadproductindex()
userquit = 0

while userquit==0:
	eplib.showmainmenu()
	try:
		selection = raw_input("Choose an action: ")
		if not int(selection):
			raise ValueError()
		else: 
			selectioni=int(selection)
		if selectioni==1:
			defineproduct()
		if selectioni==2:
			marketanalysis()
		if selectioni==3:
			checksellorders()
		if selectioni==10:
			userquit=1
	except ValueError:
		print "Please enter a number!"
		
print "Goodbye."