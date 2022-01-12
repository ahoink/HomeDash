import time
from datetime import datetime, timedelta

class MindTracker():
	def __init__(self):
		data = readData()
		self.stats = processData(data)
		self.init = False

	def getStats(self):
		t = time.time()
		last_dt = datetime.fromtimestamp(self.stats["last"])
		now_dt = datetime.fromtimestamp(t)
		if (now_dt - last_dt) > timedelta(days=1, hours=23, minutes=59):
			self.stats["current_streak"] = 0
 			
		return self.stats

	def addSession(self, duration):
		t = time.time()
		writeSession(t, duration)

		last_dt = datetime.fromtimestamp(self.stats["last"])
		this_dt = datetime.fromtimestamp(t)
		if isNextDay(last_dt, this_dt):
			self.stats["current_streak"] += 1
			self.stats["best_streak"] = max(self.stats["best_streak"], self.stats["current_streak"])
		else:
			self.stats["current_streak"] = 1
		self.stats["sessions"] += 1
		self.stats["total"] += duration
		self.stats["last"] = t

		return True

def readData():
	data = []
	with open("data/mindfulness.csv", 'r') as f:
		data = f.readlines()
	data = [d.replace("\n", "") for d in data]

	return data

def writeSession(t, duration):
	with open("data/mindfulness.csv", 'a') as f:
		f.write("%d,%d\n" % (t, duration))

def isNextDay(dt1, dt2):
	next_day = dt1 + timedelta(days=1)
	return next_day.day == dt2.day and next_day.month == dt2.month and next_day.year == dt2.year

def processData(data):
	stats = {}

	best_streak = 1
	curr_streak = 1
	num_sessions = 0
	tot_time = 0

	prev_day = datetime.fromtimestamp(0)
	last_ts = 0
	for line in data:
		splitted = line.split(',')
		ts = int(splitted[0])
		dur = int(splitted[1])

		# streaks
		dt = datetime.fromtimestamp(ts)
		if isNextDay(prev_day, dt):
			curr_streak += 1
		elif prev_day.day == dt.day:
			pass
		else:
			curr_streak = 1
		best_streak = max(best_streak, curr_streak)
		prev_day = dt

		last_ts = ts
		tot_time += dur
		num_sessions += 1

	stats["best_streak"] = best_streak
	stats["current_streak"] = curr_streak
	stats["sessions"] = num_sessions
	stats["total"] = tot_time
	stats["last"] = last_ts

	return stats
