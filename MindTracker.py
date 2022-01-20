import time
from datetime import datetime, timedelta
from PIL import Image

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

def genGridPlot():
	data = readData()

	# dimension vars
	sq_size = 30
	spacing = 5
	grid_size = sq_size + spacing
	width = grid_size*7-spacing
	height = grid_size*5-spacing
	x = 0
	y = 0

	# image vars
	img = Image.new("RGBA", (width, height), (30, 30, 30, 0))
	px = img.load()

	# prepare data
	dt_now = datetime.fromtimestamp(time.time())
	organized_data = []
	day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
	first_day = ""
	max_dur = 0
	prev_day = None

	for d in data:
		splitted = d.split(',')
		ts = int(splitted[0])
		dur = int(splitted[1])
		dt = datetime.fromtimestamp(ts)
		if dt < (dt_now - timedelta(days=30)):
			continue
		#print(dt)
		if first_day == "":
			first_day = time.strftime("%A", time.localtime(ts))
			prev_day = dt - timedelta(days=1)

		if prev_day.day == dt.day:
			organized_data[-1] += dur
		else:
			prev_day += timedelta(days=1)
			while prev_day.day != dt.day:
				organized_data.append(0)
				prev_day += timedelta(days=1)
			organized_data.append(dur)
		max_dur = max(max_dur, dur)
		prev_day = dt

	# draw data
	#print(len(organized_data))
	#print(organized_data)
	x = day_names.index(first_day) * grid_size
	for d in organized_data:
		color = colorGradient(d / max_dur)
		for j in range(y, y+sq_size):
			for i in range(x, x+sq_size):
				px[i, j] = color
		x += grid_size
		if x >= width:
			x = 0
			y += grid_size

	return img

def colorGradient(pct):
	r = 0
	g = int(127*pct)
	b = int(255*pct)
	return (r, g, b, 255)
		
	
