#!/usr/bin/python

# EPITHAL
# Main functions/workflow
# TODO? move some of this to eplib.py

import os
import json
import eveapi
import presetup
import eplib
from operator import itemgetter

# As defined by ESI cache control headers, but we're not parsing those yet
cachetime_market = 600

# Load all the item names from names.json
eplib.loadnames()

# Load the trade hubs
tradehubs=eplib.loadtradehubs()

# These will be filled in when we pick a portfolio
products=[]
productcount=0

# Search ESI for the lowest priced sell order of a given item, in a given hub, with a given quantity
# Returns -1 if no suitable sell order exists
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

# Run an ESI-powered price check on all hubs
def checksellorders():
	typeid = eplib.takenameinput("Enter product to price-check: ")
	if(typeid < 1):
		print "No matching item found."
	else:
		print
		for hub in tradehubs:
			price = findlowestsellpricewithquant(hub, typeid, 1)
			print hub["hubname"].rjust(20) + ": {:,.2f}".format(price)	
			
def loadproductindex():
	global products
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

# List all products in current portfolio	
def showproductindex():
	i=1
	print
	for prod in products:
		print str(i) + ") " + prod["nickname"]
		i+=1
	
# Defines a product as a set of input materials and output
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
			
	#step 3: define an output quantity
			
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
	
	#outpath=selectdestportfolio()
	
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
	
def dictprodreport(prod,buyhub,sellhub):
	buildprice = 0
	failedbuild = 0
	json_file=os.path.join("ep_data","products",prod["filename"])
	with open(json_file) as json_data:
		proddata=json.load(json_data)
		for material in proddata["inputs"]:
			matprice = findlowestsellpricewithquant(buyhub,material["typeid"],material["quant"])
			if matprice < 0:
				failedbuild = 1
			else:
				buildprice += (matprice * material["quant"])
				
	sellprice = findlowestsellpricewithquant(sellhub,proddata["outputid"],1) * proddata["outputquant"]
	profit = sellprice-buildprice
	profitratio = profit/buildprice
	
	results = {}
	results.setdefault('prodname',prod["nickname"])
	results.setdefault('buildprice',buildprice)
	results.setdefault('failedbuild',failedbuild)
	results.setdefault('sellprice',sellprice)
	results.setdefault('profit',profit)
	results.setdefault('profitratio',profitratio)
	
	return results
	
def printresultentry(result):
	print result['prodname']
	print "{:,.2f}".format(result['sellprice']).rjust(20) + " -" + "{:,.2f}".format(result['buildprice']).rjust(20)+ " =" + "{:,.2f}".format(result['profit']).rjust(20) + " ({:.0%})".format(result['profitratio'])
		
def printprodreport(prod,buyhub,sellhub,batchsize):
	buildprice = 0
	failedbuild = 0
	print
	print "Running report on " + prod["nickname"] + "."
	print "Buying in " + buyhub["hubname"] + " selling in " + sellhub["hubname"] + "."
	print
	json_file=os.path.join("ep_data","products",prod["filename"])
	with open(json_file) as json_data:
		proddata=json.load(json_data)
#		print proddata
		for material in proddata["inputs"]:
			matprice = findlowestsellpricewithquant(buyhub,material["typeid"],material["quant"]*batchsize)
			if matprice < 0:
#				print "No suitable sell order for " + eplib.getname(material["typeid"]) + "!"
				print eplib.getname(material["typeid"]).rjust(40) + ": " + "Not for sale".rjust(15) + " x " + str(material["quant"]*batchsize)
				failedbuild = 1
			else:
				print eplib.getname(material["typeid"]).rjust(40) + ": " + str(matprice).rjust(15) + " x " + str(material["quant"]*batchsize)
			buildprice += (matprice * material["quant"]*batchsize)
			
		print
			
		if failedbuild > 0:
			print "One or more materials not for sale in sufficient quantity in "+buyhub["hubname"] + "!"
		else:
			sellprice = findlowestsellpricewithquant(sellhub,proddata["outputid"],1) * proddata["outputquant"] * batchsize
			profit = sellprice-buildprice
			profitratio = profit/buildprice
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
		prodi = eplib.inputnumber("Run report on which product? ")
		batchsize = eplib.inputnumber("Build how many batches? ")
		if prodi < 0:
			print "Please enter a valid product number."
		else:
			prodi -= 1
			buyhubi = selecthub("Select buy hub: ")
			sellhubi = selecthub("Select sell hub: ")
			printprodreport(products[prodi],tradehubs[buyhubi],tradehubs[sellhubi],batchsize)
			
	else:
		print "You need to define at least one product first."

def marketanalysismulti():
	global productcount
	analysis = []
	if(productcount>0):
		showproductindex()

		print
		prodi = raw_input("Enter a list of producs separated by spaces: ")
		buyhubi = selecthub("Select buy hub: ")
		sellhubi = selecthub("Select sell hub: ")
		
		if prodi=="all" or prodi=="a":
			for product in products:
				analysis.append(dictprodreport(product,tradehubs[buyhubi],tradehubs[sellhubi]))
		else:		
			for i in prodi.split():
				try:
					prodnum=int(i)-1
					analysis.append(dictprodreport(products[prodnum],tradehubs[buyhubi],tradehubs[sellhubi]))
				except ValueError:
					print "Skipping " + i
			
		for product in sorted(analysis, key=itemgetter('profitratio')):
			printresultentry(product)
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
#		if selectioni==1:
#			productcount=
		if selectioni==2:
			defineproduct()
		if selectioni==4:
			marketanalysis()
		if selectioni==5:
			marketanalysismulti()
		if selectioni==7:
			checksellorders()
		if selectioni==10:
			userquit=1
	except ValueError:
		print "Please enter a number!"
		
print "Goodbye."