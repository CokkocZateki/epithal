#!/usr/bin/env python

import Tkinter as tk
import eplib
import os
import json
import eveapi
#import PIL.Image
#import PIL.ImageTk

# As defined by ESI cache control headers, but we're not parsing those yet
cachetime_market = 600

tradehubs={}
portfolios={}
top=[]
activebuyhub={}
activesellhub={}
hbuttons=[]
h2buttons=[]
tbuttons=[]
hubframe=0
listframe=0
activefolio=[]
lb=[]
mainframe=0
apilabel=0

tasks = ['Edit Product','Market Analysis','Portfolio Analysis','Price Check']

def getJita():
	for hub in tradehubs:
		if hub['hubname']=='Jita':
#			print hub
			return hub
			
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


class Application(tk.Frame):
	def __init__(self, master=None):
		global tradehubs
		global portfolios
		global top
		global activesellhub
		global activebuyhub
		global activefolio
		global mainframe
		top=tk.Frame.__init__(self, master)
		top=self.winfo_toplevel()
		top.rowconfigure(0, weight=1)            
		top.columnconfigure(0, weight=1)         
		self.rowconfigure(0, weight=1)           
		self.columnconfigure(0, weight=1)        
		#photo=tk.PhotoImage(file='ep_icon.gif')
		top.tk.call('wm', 'iconbitmap', top._w, '-default', 'ep_icon.ico')

		eplib.loadnames()
		#self.grid(sticky=tk.N+tk.S+tk.E+tk.W)
		tradehubs=eplib.loadtradehubs()
		activesellhub = getJita()
		activebuyhub = getJita()
		portfolios=eplib.loadportfolios()
		activefolio=eplib.loadallproducts()
		self.createWidgets()
		self.createTopMenu()
		mainframe=tk.Frame(top)
		mainframe.grid(row=1,column=1)

		
	def setallproducts(self):
		global listframe
		global activefolio
		listframe.destroy()
		activefolio=eplib.loadallproducts()
		self.createProductList()
		
	def setnewportfolio(self, folioname):
		global listframe
		global activefolio
		listframe.destroy()
		activefolio=eplib.loadportfolio(folioname)
		self.createProductList()
		
	def productinfo(self):
		global lb
		global activefolio
		global mainframe
		index=lb.curselection()[0]
		product=activefolio[index]
		proddata=eplib.loadproductdata(product['filename'])
		#print product
		mainframe.destroy()
		mainframe=tk.Frame(top)
		l=tk.Label(mainframe, text=product['nickname'], font="bold")
		l.grid(row=0,column=0, columnspan=3, sticky=tk.N)
		i=1
		for material in proddata["inputs"]:
			l=tk.Label(mainframe, text=eplib.getname(material['typeid']))
			l2=tk.Label(mainframe, text=' x ')
			l3=tk.Label(mainframe, text=str(material['quant']))
			l.grid(row=i, column=0, sticky=tk.E)
			l2.grid(row=i, column=1)
			l3.grid(row=i, column=2, sticky=tk.W)
			i+=1
		mainframe.grid(row=1,column=1)
		
	def marketanalysis(self):
		global lb
		global activefolio
		global mainframe
		buildprice=0
		failedbuild=False
		index=lb.curselection()[0]
		product=activefolio[index]
		proddata=eplib.loadproductdata(product['filename'])
		#print product
		mainframe.destroy()
		mainframe=tk.Frame(top, bg="white", relief=tk.GROOVE, bd=5)
		l=tk.Label(mainframe, text=product['nickname'], font="bold", bg="white")
		l.grid(row=0,column=0, columnspan=3, sticky=tk.N)
		i=1
		for material in proddata["inputs"]:
			self.setapibusy()
			matprice = findlowestsellpricewithquant(activebuyhub,material["typeid"],material["quant"])
			self.setapiidle()
			l1=tk.Label(mainframe, text=(eplib.getname(material['typeid']) + ":"), bg="white")
			if matprice < 0:
				failedbuild = True
				l2=tk.Label(mainframe, text='Not for sale!', fg="red", bg="white")
#				l3=tk.Label(mainframe, text='')
			else:
				l2=tk.Label(mainframe, text=("{:,.2f} ".format(matprice)), bg="white")
				
			l3=tk.Label(mainframe, text=(' x ' + str(material["quant"])), bg="white")
				
			l1.grid(row=i, column=0, sticky=tk.E)
			l2.grid(row=i, column=1)		
			l3.grid(row=i, column=2, sticky=tk.W)
			i+=1
			buildprice += (matprice * material["quant"])
		
		sellprice = findlowestsellpricewithquant(activesellhub,proddata["outputid"],1) * proddata["outputquant"]
		profit = sellprice-buildprice
		profitratio = profit/buildprice
		
		l4=tk.Label(mainframe, text=("Sells for {:,.2f}".format(sellprice)), font="bold", bg="white")
		if failedbuild:
			l5=tk.Label(mainframe, text=("Cannot procure build materials in "+activebuyhub['hubname']), font="bold", fg="red", bg="white")
		else:
			if profit > 0:
				l5=tk.Label(mainframe, text=("Profit {:,.2f} ".format(profit) + "({:.0%})".format(profitratio)), font="bold", bg="white")
			else:
				l5=tk.Label(mainframe, text=("Loss {:,.2f} ".format(profit) + "({:.0%})".format(profitratio)), font="bold", fg="red", bg="white")
		
		l4.grid(row=i,column=0, columnspan=3, sticky=tk.S)
		l5.grid(row=i+i,column=0, columnspan=3, sticky=tk.S)
			
		mainframe.grid(row=1,column=1)	
		
	def createProductList(self):
		global listframe
		global lb
		listframe=tk.Frame(top)
		l = tk.Label(listframe, text="Products in Portfolio")
		l.pack()
		sb = tk.Scrollbar(listframe, orient=tk.VERTICAL)
		lb = tk.Listbox(listframe, height=25, width=40)
		sb.pack(side=tk.RIGHT, fill=tk.Y)
		sb.config(command=lb.yview)
		lb.config(yscrollcommand=sb.set)
		lb.pack(side=tk.LEFT, fill=tk.BOTH, expand = True)
		for prod in activefolio:
			lb.insert(tk.END,prod['nickname'])
					
		listframe.grid(row=1,column=0,sticky=tk.W)
	
	def createWidgets(self):
		global hubframe
		global hbuttons
		global h2buttons
		global tbuttond
		global apilabel
		hubframe=tk.Frame(top)
		i=0
		l = tk.Label(hubframe, text="Buy Hub Select")
		l.grid(row=0,column=0,columnspan=len(tradehubs))
#		hbuttons=[]
		for hub in tradehubs:
			hub.setdefault('index',i)
			hbuttons.append(tk.Button(hubframe, text=hub['hubname']))
			hbuttons[i].configure(command=lambda i=i: self.setbuyhub(i))
			if activebuyhub['index']==i:
				hbuttons[i].configure(relief=tk.SUNKEN)
			hbuttons[i].grid(row=1,column=i)
			i+=1
					
		l2 = tk.Label(hubframe, text="Sell Hub Select")
		l2.grid(row=2,column=0,columnspan=len(tradehubs))
#		hbuttons=[]
		i=0
		for hub in tradehubs:
			hub.setdefault('index',i)
			h2buttons.append(tk.Button(hubframe, text=hub['hubname']))
			h2buttons[i].configure(command=lambda i=i: self.setsellhub(i))
			if activesellhub['index']==i:
				h2buttons[i].configure(relief=tk.SUNKEN)
			h2buttons[i].grid(row=3,column=i)
			i+=1
			
		hubframe.grid(row=0,column=0,sticky=tk.NW)
		
		taskframe=tk.Frame(top)
		i=0
		l = tk.Label(taskframe, text="Task Select")
		l.pack()
		tbuttons.append(tk.Button(taskframe, text="Product Info", command=self.productinfo))
		tbuttons[i].pack(side=tk.LEFT)
		i+=1
		tbuttons.append(tk.Button(taskframe, text="Market Analysis", command=self.marketanalysis))
		tbuttons[i].pack(side=tk.LEFT)
		for task in tasks:
			tbuttons.append(tk.Button(taskframe, text=task))
			tbuttons[i].pack(side=tk.LEFT)
			i+=1	
			
		taskframe.grid(row=0,column=1,sticky=tk.N)
		
		apiframe=tk.Frame(top)
		apilabel=tk.Label(apiframe, text="API idle.")
		apilabel.pack()
		apiframe.grid(row=2,column=0,sticky=tk.SW)	
		
		self.createProductList()
		
	def setapiidle(self):
		global apilabel
		apilabel.configure(text="API Idle.")
		apilabel.update()
				
	def setapibusy(self):
		global apilabel
		apilabel.configure(text="API Working....")
		apilabel.update()
		
	def setsellhub(self, hubidx):
		global activesellhub
		for hub in tradehubs:
			if hub['index'] == hubidx:
				activesellhub=hub
		i=0
		for button in h2buttons:
			if activesellhub['index']==i:
				h2buttons[i].configure(relief=tk.SUNKEN)
			else:
				h2buttons[i].configure(relief=tk.RAISED)
			i+=1
		
	def setbuyhub(self, hubidx):
		global activebuyhub
		for hub in tradehubs:
			if hub['index'] == hubidx:
				activebuyhub=hub
		i=0
		for button in hbuttons:
			if activebuyhub['index']==i:
				hbuttons[i].configure(relief=tk.SUNKEN)
			else:
				hbuttons[i].configure(relief=tk.RAISED)
			i+=1
		
		#self.quit = tk.Button(self, text='Quit', command=self.quit)
		#self.quit.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
	
	def createTopMenu(self):
		top = self.winfo_toplevel()
		self.menuBar = tk.Menu(top)
		top['menu'] = self.menuBar
		
		self.FileMenu = tk.Menu(self.menuBar)
		self.menuBar.add_cascade(label='File', menu=self.FileMenu)
		self.FileMenu.add_command(label='Quit', command=self.quit)
		
#		self.HubsMenu = tk.Menu(self.menuBar)
#		self.menuBar.add_cascade(label='Hubs', menu=self.HubsMenu)
#		for hub in tradehubs:
#			self.HubsMenu.add_radiobutton(label=hub['hubname'])
			
		self.FolioMenu = tk.Menu(self.menuBar)
		self.menuBar.add_cascade(label='Portfolios', menu=self.FolioMenu)
		self.FolioMenu.add_radiobutton(label='All Products', command=self.setallproducts)
		i=0
		for folio in portfolios:
			self.FolioMenu.add_radiobutton(command=lambda folio=folio: self.setnewportfolio(folio), label=folio)
			i+=1
		
		self.HelpMenu = tk.Menu(self.menuBar)
		self.menuBar.add_cascade(label='Help', menu=self.HelpMenu)
		self.HelpMenu.add_command(label='About') #, command=self.__aboutHandler)
		
	def setportfolio(self,folioname):
		return

app = Application()
app.master.title('EPITHAL')
#im=PIL.image.open('ep_icon.gif')
#photo=PIL.ImageTk.PhotoImage(im)

app.mainloop()
