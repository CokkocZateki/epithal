#!/usr/bin/python

# EPITHAL
# Defines various functions for use in main loop.

import eveapi
import json
import os

def showlogo():
	print
	print "	(E)ve"
	print "	(P)ython"
	print "	(I)ndustrial"
	print "	(T)ool"
	print "	(H)elper"
	print "	(A)nd"
	print "	(L)ogic"

	
def loaditems():
	# pull all market items from ESI
	json_file=eveapi.pullfromcache("markets/prices/",3600)
	with open(json_file) as json_data:
		items=json.load(json_data)
		return items

def loadnames():
	json_file=os.path.join("ep_data","names.json")
	with open(json_file) as json_data:
		names=json.load(json_data)
		return names
		
def showmainmenu():
	print
	print "(1) Define new product"
	print "(2) Market analysis on products"
	print "(3) Check sell orders for an item"
	print "(10) Quit"
	print

def loadtradehubs():
	hubsfile = os.path.join("ep_data","tradehubs.json")
	if not os.path.exists(hubsfile):
		print "No trade hubs defined found."
		return 0
	else:
		with open(hubsfile) as hub_data:
			tradehubs=json.load(hub_data)
			return tradehubs
