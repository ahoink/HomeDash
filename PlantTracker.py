import time
from datetime import datetime

MAX_SCORE = 1.5
FREQ_MA = 3

class PlantTracker():
	def __init__(self):
		self.plants = readData()
		self.freqs = getFreqs()
		self.prev_state = [[x for x in y] for y in self.plants]
		self.init = False
		self.scorePlants()
	
	def scorePlants(self):
		# score is the ratio of time since last completed over expected frequency (with a max cap)
		tnow = time.time()
		for i in range(len(self.plants)):
			p = self.plants[i]
			freq = self.freqs.get(p[0], 0)
			score = (tnow - p[1]) / freq if freq > 0 else 1
			# Data file doesn't include score, so it may not exist yet if file was just read
			if not self.init: self.plants[i].append(score)
			else: self.plants[i][-1] = score
		self.init = True

	def getPlantList(self):
		self.scorePlants()
		plnts = []
		hdrs = ["Plant", "Last Watered", "Frequency"]
		sorted_plants = sorted(self.plants, key=lambda x: x[0], reverse=True) # sort by name
		for p in sorted_plants:
			temp = {}
			temp[hdrs[0]] = p[0] 											# Plant name
			temp[hdrs[1]] = time.strftime("%b %d", time.localtime(p[1]))	# Last watered (Month Date)
			temp[hdrs[2]] = secToTimeString(self.freqs.get(p[0], 0))		# Avg watering frequency
			temp["Color"] = self.getColorFromScore(p[-1])					# Color hex code
			plnts.append(temp)	
		return {"Headers":hdrs, "Plants":plnts}

	def getColorFromScore(self, score):

		# generate hex string of color based on the score (lowest RGB value is 128 so the color is lighter and softer)
		# Start as green and fade to yellow as score approaches half of the max score
		if score <= (MAX_SCORE/2):
			r = "%0.2X" % int(128 + 128 * (score / (MAX_SCORE/2)))
			g = "FF"
			b = "80"
		# fade from yellow to red as score approaches max score
		elif score < MAX_SCORE:
			r = "FF"
			g = "%0.2X" % int(255 - 128 * ((score-(MAX_SCORE/2)) / (MAX_SCORE/2)))
			b = "80"
		else:
			return "#FF8080"
		return "#%s%s%s" % (r, g, b)

	def addPlant(self, name):
		if not name or name in [n[0] for n in self.plants]:
			return "Invalid Name"

		# save the current state and add the new plant with last completed time as now
		self.prev_state = [[x for x in y] for y in self.plants]
		self.plants.append([name, time.time()])
		saveData(self.plants)
		return "sall good"
	
	def updatePlant(self, plant_name):
		tnow = time.time()
		# get sublist from plant list where name matches plant_name and get the index of that sublist
		sublist = [x for x in self.plants if x[0] == plant_name][0]
		idx = self.plants.index(sublist)

		# save the current state before updating
		self.prev_state = [[x for x in y] for y in self.plants]

		# update plant last completed time and save to file
		self.plants[idx][1] = tnow
		saveData(self.plants)
		writeUpdate(plant_name, tnow)

		# recalc avg frequencies
		self.freqs = getFreqs()

		resp = [time.strftime("%b %d", time.localtime(tnow))]
		return resp

	def revertPrevState(self):
		if len(self.plants) == len(self.prev_state):
			remLastStatEntry()
		self.plants = [[x for x in y] for y in self.prev_state]
		saveData(self.plants)
		return "sall good"

def readData():
	plants = []
	with open("data/plants.csv", 'r') as f:
		plants = f.readlines()
	plants = plants[1:]
	plants = [t.replace("\n","").split(',') for t in plants]
	for i in range(len(plants)):
		plants[i][1] = int(plants[i][1]) # last completed timestamp
	return plants

def saveData(data):
	with open("data/plants.csv", 'w') as f:
		f.write("plant,last_watered\n")
		for p in data:
			f.write("%s,%d\n" % (p[0], p[1]))

def readStats():
	stats = []
	with open("data/plant_stats.csv", 'r') as f:
		stats = f.readlines()
	return stats

def writeUpdate(plant, t):
	with open("data/plant_stats.csv", 'a') as f:
		f.write("%s,%d\n" % (plant, t))

def remLastStatEntry():
	data = []
	with open("data/plant_stats.csv", 'r') as f:
		data = f.readlines()
	data = data[:-1]
	with open("data/plant_stats.csv", 'w') as f:
		for d in data:
			f.write(d)

def getFreqs():
	stats = readStats()
	stats = stats[::-1]
	plant_times = {}
	plant_freqs = {}
	for s in stats:
		splitted = s.replace("\n", "").split(',')
		temp = plant_times.get(splitted[0], [])
		if len(temp) >= (FREQ_MA + 1): continue
		temp.append(int(splitted[1]))
		plant_times[splitted[0]] = temp

	for p in plant_times:
		times = plant_times[p]
		avg = 0
		num = min(len(times)-1, FREQ_MA)
		if num < 1: continue
		for i in range(num):
			avg += times[i] - times[i+1]
		avg /= num
		plant_freqs[p] = avg
	return plant_freqs

def secToTimeString(t, whole=False):
	# only converts to days or months
	days = t / 86400
	if whole:
		days = int(days + 0.5)
		if days < 1:
			timestr = "N/A"
		elif days == 1:
			timestr = "Daily"
		elif days < 7:
			timestr = "%d days" % days
		elif days <= 28:
			timestr = "%d wks" % (days/7+0.5)
		else:
			timestr = "%d mon" % (days/30+0.5)
	else:
		if days <= 28:
			timestr = "%d d" % (days+0.5)
		else:
			timestr = "%d w" % (days / 7+0.5)
	return timestr

if __name__ == "__main__":
	print("Not intended to be run as main program")
