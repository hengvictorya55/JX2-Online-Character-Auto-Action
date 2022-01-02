import psutil
import pymem
import os
import sys
import win32com.shell.shell as shell
import time
import binascii
import threading
import datetime


class JXHero():
	def __init__(self, proc):
		self.proc = proc
		self.pymem = pymem.Pymem()
		self.pymem.open_process_from_id(self.proc.pid)
		self.baseAddress = self.pymem.base_address
	
	def getAddressPointer(self, start, pointer):
		addr = start
		addr = self.pymem.read_int(addr)
		for p in pointer:
			addr = self.pymem.read_int(addr + p)
		return addr
	
	def getStringFromAddress(self, address):
		b = self.pymem.read_bytes(address, 1)
		if(b == b'\x00'):
			return ""
		else:
			return b.decode() + self.getStringFromAddress(address+1)
		
	def getHeroName(self):
		try:
			addr = self.getAddressPointer(self.baseAddress+0x548A08, [0x270A8C,0x0,0x4,0x88]) + 0x44
			return self.getStringFromAddress(addr)
		except:
			return ""
	
	playersNearByBaseAddr = 0
	def getPlayersNearBy(self):
		playersNearBy = []
		if(self.playersNearByBaseAddr==0):
			self.playersNearByBaseAddr = self.getAddressPointer(self.baseAddress+0x548A08, [0x270A90,0x0])
		offset = 0x4
		for i in range(300):
			try:
				player = self.getAddressPointer(self.playersNearByBaseAddr+offset, [])				
				playerName = self.getStringFromAddress(player + 0x44)
				if(playerName!=""):
					playersNearBy.append({'name': playerName, 'id': player, 'hugId': self.getAddressPointer(player+0x4, [])})
			except:
				pass
			offset+=0x4
		return playersNearBy
	
	def AOBScan(self, hexString, startAddress):
		hexBytes = bytes.fromhex(hexString)
		curAddr = startAddress
		while True:
			for i in range(len(hexBytes)):
				if(self.pymem.read_bytes(curAddr+i, 1) == hexBytes[i:i+1]):
					if(i==len(hexBytes)-1):
						return curAddr
					continue
				break	
			curAddr+=1
	
	def testHugId(self):
		a = pymem.pattern.pattern_scan_module(self.pymem.process_handle, pymem.process.module_from_name(self.pymem.process_handle, "SO2Game.exe"), bytes.fromhex("51 69 61 6E 5A 68 75 61 6E 67 44 61 59 61 6E 67"))
		return a
	hugId = 0
	hugPlayerMem = 0
	def hug(self, playerId):
		if(self.hugId == 0):
			self.pymem.write_int(5182001, 0x7405F883)
			self.hugId = pymem.pattern.pattern_scan_module(self.pymem.process_handle, pymem.process.module_from_name(self.pymem.process_handle, "SO2Game.exe"), bytes.fromhex("51 69 61 6E 5A 68 75 61 6E 67 44 61 59 61 6E 67")) - 79
			self.hugId = self.getAddressPointer(self.hugId, [])
			
			new = (self.pymem.allocate(4096))
			self.hugPlayerMem = new
			
			self.pymem.write_int(new+4,self.hugId)
			hex_val = ("50 6A 05 FF 35 00 00 A7 00 8B 0D 00 00 A7 00 81 C1 C8 31 00 00 B8 60 10 4F 00 FF D0 58 C3")
			self.pymem.write_bytes(new+20+8,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
			self.pymem.write_int(new+20+13,new)
			self.pymem.write_int(new+20+19,new+4)
			
			
			#reduce call load
			hex_val = ("EB")
			self.pymem.write_bytes(0x004E1306,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
			
			hex_val = ("90 90 90 90 90")
			self.pymem.write_bytes(0x004E12F3,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
			hex_val = ("90 90 90 90 90")
			self.pymem.write_bytes(0x004E12FE,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
			hex_val = ("90 90 90 90 90")
			self.pymem.write_bytes(0x004E135B,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
			hex_val = ("90 90 90 90 90")
			self.pymem.write_bytes(0x004E365,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
			hex_val = ("90 90 90 90 90")
			self.pymem.write_bytes(0x004E1374,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
			
			hex_val = ("C2 0C 00")
			self.pymem.write_bytes(0x004E1630,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
			
			#hug all pk
			hex_val = ("EB 37")
			self.pymem.write_bytes(0x004E1246,bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
		
		self.pymem.write_int(self.hugPlayerMem,self.getAddressPointer(playerId+0x4, []))
		self.pymem.start_thread(self.hugPlayerMem+20+8)
		
	def blockHug(self):
		new0 = (self.pymem.allocate(4096))
		self.pymem.write_int(new0+0, 0x006F6F78)
		
		new = (self.pymem.allocate(4096))
		hex_val = ("81 3C 24 56 34 12 00 75 03 C2 0C 00 55 8B 6C 24 0C 85 ED 57 FF 25")
		address = new
		self.pymem.write_bytes(address, bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
		self.pymem.write_int(address+3, 0x004E1436)
		self.pymem.write_int(address+len(bytes.fromhex(hex_val)), new0)
		
		self.pymem.write_int(new0+4, new)
		
		hex_val = ("FF 25")
		address = 0x006E6F70
		self.pymem.write_bytes(address, bytes.fromhex(hex_val),len(bytes.fromhex(hex_val)))
		self.pymem.write_int(address+2,new0+4)

listHeroToHug = []
myHeroName = []
def process(jxHero):
	while True:
		try:
			allPlayer = jxHero.getPlayersNearBy()
			for player in allPlayer:
				if((player['name'].lower() in listHeroToHug or "all" in listHeroToHug) and player['name'].lower() not in myHeroName):
					jxHero.hug(player['id'])
					time.sleep(0.01)
			time.sleep(0.01)
		except:
			pass
	
def main():
	date = datetime.date(2025,1,1)
	date_of_today = datetime.date.today()
	if(date_of_today>date):
		return
	jxProcScan = [process for process in psutil.process_iter() if process.name() == "SO2Game.exe"]
	jxHeros = {}
	i = 1
	for proc in jxProcScan:
		try:
			jxHero = JXHero(proc)
			jxHero.blockHug()
			if(jxHero.getHeroName()!=""):
				jxHeros.update({str(i): jxHero})
				myHeroName.append(jxHero.getHeroName())
				i+=1
		except:
			pass
	
	print("=====List all JX heros:=====")
	for key in jxHeros:
		print("["+key+"]" + ": " + jxHeros[key].getHeroName() +"     "+str(jxHeros[key].testHugId())) 
	heroInputs = input("Please enter which game process you want to automate (separated by comma): ").split(",")
	if("all" in heroInputs):
		heroInputs=jxHeros
	for i in heroInputs:
		try:
			th = threading.Thread(target=process, args=(jxHeros[i],), daemon=True)
			th.start()
		except:
			pass
	while True:
		listHeroToHug.append(input("Enter name hero to hug: ").lower())
		
if __name__ == "__main__":
	main()
	input("Exit")

	
	
