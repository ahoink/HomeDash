import time
from datetime import datetime, timedelta

class MindTracker():
	def __init__(self):
		data = readData()
		self.stats = processData(data)
		self.init = False

	def getStats(self):
		return self.stats

	def addSession(self, duration):
		writeSession(time.time(), duration)
		self.stats["current_streak"] += 1
		self.stats["sessions"] += 1
		self.stats["total"] += duration

def readData():
	data = []
	with open("data/mindfulness.csv", 'r') as f:
		data = f.readlines()
	data = [d.replace("\n", "") for d in data]

	return data

def writeSession(t, duration):
	with open("data/mindfulness.csv", 'a') as f:
		f.write("%d,%d\n" % (t, duration))

def processData(data):
	stats = {}

	best_streak = 1
	curr_streak = 1
	num_sessions = 0
	tot_time = 0

	prev_day = datetime.fromtimestamp(0)
	for line in data:
		splitted = line.split(',')
		ts = int(splitted[0])
		dur = int(splitted[1])

		# streaks
		dt = datetime.fromtimestamp(ts)
		temp_dt = prev_day + timedelta(days=1)
		if temp_dt.day == dt.day and temp_dt.month == dt.month and temp_dt.year == dt.year:
			curr_streak += 1
		elif prev_day.day == dt.day:
			pass
		else:
			curr_streak = 1
		best_streak = max(best_streak, curr_streak)
		prev_day = dt

		tot_time += dur
		num_sessions += 1

	stats["best_streak"] = best_streak
	stats["current_streak"] = curr_streak
	stats["sessions"] = num_sessions
	stats["total"] = tot_time

	return stats
