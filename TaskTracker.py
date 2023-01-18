import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import copy

MAX_SCORE = 1.5
WMA_INT = 10

class TaskTracker():
	def __init__(self):
		self.tasks = readData()
		self.prev_state = copy.deepcopy(self.tasks)
		self.init = False
		self.last_action = ""
	
	def scoreTasks(self):
		# score is the ratio of time since last completed over expected frequency (with a max cap)
		tnow = time.time()
		for t in self.tasks:
			task = self.tasks[t]
			score = (tnow - task["last"]) / task["freq"]
			if not task["isActive"]:
				score = 0.0
			task["score"] = score
		self.init = True

	def getTaskList(self, todayOnly=False):
		self.scoreTasks()
		tsks = []
		hdrs = ["Task", "Last", "Due"]
		sorted_tasks = sorted(self.tasks.keys(), key=lambda x: self.tasks[x]["score"], reverse=True) # sort in order of score (high to low)
		for t in sorted_tasks:
			task = self.tasks[t]
			temp = {}
			temp[hdrs[0]] = t														# Task name
			temp[hdrs[1]] = time.strftime("%b %d", time.localtime(task["last"]))	# Last completed (Month Date)
			temp[hdrs[2]] = secToTimeString(task["freq"]-task["score"]*task["freq"], whole=True)			# Due
			temp["Color"] = self.getColorFromScore(task["score"])					# Color hex code
			if not task["isActive"]:
				temp["Due"] = "N/A"
			if todayOnly and temp["Due"] != "Today" and temp["Due"] != "Overdue":
				continue
			tsks.append(temp)	
		return {"Headers":hdrs, "Tasks":tsks}

	def getProductivity(self):
		data = readStats()
		task_data = readData()
		prod = processStatsData(data, task_data, retDaily=False)
		# adjust prod score for any overdue tasks
		for t in self.tasks:
			task = self.tasks[t]
			if task["score"] > 1.0:
				prod.append((normalizeScore(task["score"]) * task["weight"], task["weight"]))
		curr_prod_val = sum([p[0] for p in prod[-WMA_INT:]]) / sum([p[1] for p in prod[-WMA_INT:]])
		if curr_prod_val < 80:
			r = "E0"
			g = "%0.2X" % int(224 * (curr_prod_val/80))
			b = "00"
		else:
			r = "%0.2X" % int(224 -  224 * (curr_prod_val-80)/20)
			g = "E0"
			b = "00"
		return {"val": "%d%%" % (curr_prod_val + 0.5), "color": "#%s%s%s" % (r, g, b)}

	def getTaskInfo(self, task_name):
		temp = dict(self.tasks[task_name])
		temp["freq"] = secToTimeString(temp["freq"])
		return temp

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

	def addTask(self, name, freq, cost, wt):
		if not name or name in self.tasks:
			return "Invalid Name"
		if not freq:
			return "Invalid Frequency"

		# If freq only contains numbers, treat it as days
		if freq.isdigit():
			freq = int(freq) * 86400
		elif not freq[-1].isalpha():
			return "Invalid Frequency"
		else: # otherwise extract the "unit" (ex: for "2w" extract the 'w' and treat 2 as weeks)
			unit = freq[-1].lower()
			freq = int(freq[:-1])
			if unit == "d":
				freq *= 86400
			elif unit == "w":
				freq *= 86400 * 7
			elif unit == "m":
				freq *= 86400 * 30
			else:
				return "Invalid Frequency"

		# save the current state and add the new task with last completed time as now
		self.prev_state = copy.deepcopy(self.tasks)
		self.tasks[name] = {
			"last": time.time(),
			"freq": freq,
			"timecost": cost,
			"weight": wt,
			"isActive": 1
		}
		saveData(self.tasks)
		return "sall good"
	
	def updateTask(self, task_name):
		tnow = time.time()
		status = "OK"
		if (tnow - self.tasks[task_name]["last"]) > 86400:

			self.scoreTasks()

			# save the current state before updating
			self.prev_state = copy.deepcopy(self.tasks)

			# save the task and score upon completion to the stats file
			saveStats(task_name, self.tasks[task_name], tnow)

			# update task last completed time and save to file
			self.tasks[task_name]["last"] = tnow
			saveData(self.tasks)
		else:
			status = "DUPLICATE"
		resp = [time.strftime("%b %d", time.localtime(tnow)), "DONE", status]
		return resp

	def editTask(self, name, freq, cost, wt, last, isActive):
		if not name or name not in self.tasks:
			return "Invalid Name"
		if not freq:
			return "Invalid Frequency"

		# If freq only contains numbers, treat it as days
		if freq.isdigit():
			freq = int(freq) * 86400
		elif not freq[-1].isalpha():
			return "Invalid Frequency"
		else: # otherwise extract the "unit" (ex: for "2w" extract the 'w' and treat 2 as weeks)
			unit = freq[-1].lower()
			try:
				freq = int(freq[:-1])
			except:
				return "Invalid Frequency"
			if unit == "d":
				freq *= 86400
			elif unit == "w":
				freq *= 86400 * 7
			elif unit == "m":
				freq *= 86400 * 30
			else:
				return "Invalid Frequency"

		self.prev_state = copy.deepcopy(self.tasks)

		self.tasks[name]["freq"] = freq
		self.tasks[name]["timecost"] = cost
		self.tasks[name]["weight"] = wt
		self.tasks[name]["last"] = last
		self.tasks[name]["isActive"] = isActive

		saveData(self.tasks)
		if last != self.prev_state[name]["last"]:
			if not editLastCompletedTime(name, last):
				return "Error occurred updating timestamp"

		return "sall good"

	def setLastAction(self, action):
		self.last_action = action

	def getLastAction(self):
		return self.last_action

	def revertPrevState(self):
		if self.last_action == "":
			return "nothing to undo"

		cmd = self.last_action.split(' ')[0]
		if cmd == "UPDATE":
			#if len(self.tasks.keys()) == len(self.prev_state.keys()):
			remLastStatEntry()
		if cmd == "UPDATE" or cmd == "ADD":
			self.tasks = copy.deepcopy(self.prev_state)
			saveData(self.tasks)
			return "sall good"
		else:
			return "nothing to undo"

def readData():
	tasks = {}
	data = []
	with open("data/tasks.csv", 'r') as f:
		data = f.readlines()
	data = data[1:]
	data = [t.replace("\n","").split(',') for t in data]
	for i in range(len(data)):
		name = data[i][0]
		tasks[name] = {
			"last": int(data[i][1]),
			"freq": int(data[i][2]),
			"timecost": int(data[i][3]),
			"weight": int(data[i][4]),
			"isActive": int(data[i][5])
		}
		
		#data[i][1] = int(data[i][1]) # last completed timestamp
		#data[i][2] = int(data[i][2]) # frequency
		#data[i][3] = int(data[i][3]) # time cost
		#data[i][4] = int(data[i][4]) # weight
		#data[i][5] = int(data[i][5]) # active
	return tasks#data

def saveData(data):
	with open("data/tasks.csv", 'w') as f:
		f.write("task,last_completed,frequency,timecost,weight,active\n")
		for t in data:
			f.write("%s,%d,%d,%d,%d,%d\n" % 
			(t, data[t]["last"], data[t]["freq"], data[t]["timecost"], data[t]["weight"], data[t]["isActive"]))
			#(t[0], t[1], t[2], t[3], t[4], t[5]))

def readStats():
	data = []
	with open("data/stats.csv", 'r') as f:
		data = f.readlines()
	data = [x.replace("\n","").split(',') for x in data]
	for i in range(len(data)):
		data[i][1] = int(data[i][1]) # timestamp
		data[i][2] = int(data[i][2]) # frequency
		data[i][3] = float(data[i][3]) # score
		data[i][4] = int(data[i][4]) # time cost
		data[i][5] = int(data[i][5]) # weight
	return data

def saveStats(task, data, t):
	with open("data/stats.csv", "a") as f:
		f.write("%s,%d,%d,%f,%d,%d\n" % (task, t, data["freq"], data["score"], data["timecost"], data["weight"]))

def remLastStatEntry():
	data = []
	with open("data/stats.csv", 'r') as f:
		data = f.readlines()
	data = data[:-1]
	with open("data/stats.csv", 'w') as f:
		for d in data:
			f.write(d)

def editLastCompletedTime(task_name, t):
	data = readStats()
	idx = -1
	idx_new = -1
	for i in range(len(data)-1,0,-1):
		# Find task and update score and timestamp
		if idx < 0 and task_name in data[i][0]:
			last1 = -(data[i][3] * data[i][2] - data[i][1])
			new_score = (t - last1) / data[i][2]
			data[i][1] = t
			data[i][3] = new_score

			idx = i
			continue
		# find new position to place the task
		if idx >= 0 and data[i][1] < data[idx][1]:
			idx_new = i+1
			break

	if idx_new < 0:
		print("ERROR: Could not find a stat point earlier than %d" % data[idx][1])
		return False

	# reorder stats to move task to new position
	# keep all up until target task's new position (new_idx)
	# add in target task data (from position idx)
	# concat data up until the target task's old position
	# skip the target task's old position and concat the rest of the data through the end
	data = data[:idx_new] + [data[idx]] + data[idx_new:idx] + data[idx+1:]

	with open("data/stats.csv", "w") as f:
		for d in data:
			f.write("%s,%d,%d,%f,%d,%d\n" % (d[0], d[1], d[2], d[3], d[4], d[5]))
	return True


def normalizeScore(score):
	return 100 * (1 - min(1, max(0, score-1)))	


def processStatsData(data, tasks, retDaily=True):
	productivity = []
	daily_prod = []
	completed = []
	tot_score = 0.0
	curr_date = datetime.fromtimestamp(time.time())
	today_dt = datetime.fromtimestamp(time.time())
	past_year = curr_date - timedelta(days=365)
	task_stats = {}
	days_stats = {}
	weights = {}
	time_cost = {}
	for t in tasks:
		weights[t] = tasks[t]["weight"]
		time_cost[t] = tasks[t]["timecost"]
	for i in range(len(data)):
		task_name = data[i][0]
		task_completed = data[i][1]
		task_freq = data[i][2]
		task_score = data[i][3]
		task_cost = data[i][4]
		task_weight = data[i][5]

		if task_name not in tasks: 
			continue
		if task_name not in completed:
			completed.append(task_name)

		day = time.strftime("%A", time.localtime(task_completed))
		dt = datetime.fromtimestamp(task_completed)
		tasks[task_name]["last"] = task_completed
		if dt < past_year: continue
		prod_score = normalizeScore(task_score)
		#productivity.append((prod_score * weights[task_name], weights[task_name]))
		# increment number for tasks performed on this day
		days_stats[day] = days_stats.get(day, 0) + task_cost
		days_stats["tot"] = days_stats.get("tot", 0) + task_cost


		# keep track of which days each tasks gets completed, num times completed, and total score
		temp = task_stats.get(task_name, {"days":[], "completed":0, "score":0, "freq":0})
		temp["days"].append(day)
		temp["completed"] += 1
		temp["score"] += task_score
		temp["freq"] = task_freq
		task_stats[task_name] = temp
		
		# need at least WMA_INT elements before calculating weight moving average
		if len(productivity) < WMA_INT:
			productivity.append((prod_score * task_weight, task_weight))
			curr_date = datetime(dt.year, dt.month, dt.day, 23, 59, 59)
		# fill in gaps in daily productivity
		else:
			productivity.append((prod_score * task_weight, task_weight))
			while dt > curr_date:
				ts = datetime.timestamp(curr_date)
				temp_prod = productivity[-WMA_INT:]
				# account for overdue tasks
				for t in tasks:
					if t not in completed: continue
					temp_score = (ts - tasks[t]["last"]) / tasks[t]["freq"]
					if not tasks[t]["isActive"]: temp_score = 0.0
					if temp_score > 1.0:
						temp_prod.append((normalizeScore(temp_score) * tasks[t]["weight"], tasks[t]["weight"]))
				# calc weighted average productivity score
				daily_score = sum([p[0] for p in temp_prod[-WMA_INT:]]) / sum([p[1] for p in temp_prod[-WMA_INT:]])
				daily_prod.append((ts, daily_score))
				curr_date += timedelta(days=1)
			curr_date = datetime(dt.year, dt.month, dt.day, 23, 59, 59)

	# get daily score for today
	while today_dt >= curr_date:
		ts = datetime.timestamp(curr_date)
		temp_prod = productivity[-WMA_INT:]
		# account for overdue tasks
		for t in tasks:
			if t not in completed: continue
			temp_score = (ts - tasks[t]["last"]) / tasks[t]["freq"]
			if not tasks[t]["isActive"]: temp_score = 0.0
			if temp_score > 1.0:
				temp_prod.append((normalizeScore(temp_score) * tasks[t]["weight"], tasks[t]["weight"]))
		# calc weighted average productivity score
		daily_score = sum([p[0] for p in temp_prod[-WMA_INT:]]) / sum([p[1] for p in temp_prod[-WMA_INT:]])
		daily_prod.append((ts, daily_score))
		curr_date += timedelta(days=1)

	if retDaily:
		return daily_prod, days_stats, task_stats
	else:
		return productivity

def plotStats():
	stat_data = readStats()
	task_data = readData()
	productivity, days_stats, task_stats = processStatsData(stat_data, task_data)

	gridplot, gridstart = genGridPlot(productivity)
	use_gridplot = False

	ma = []
	ma = [p[1] for p in productivity]

	# create xtick points and labels for the start of each month
	xticks = []
	xlabels = []
	for i in range(len(productivity)):
		dt = datetime.fromtimestamp(productivity[i][0])
		if dt.day == 1:
			if use_gridplot:
				xticks.append(int((i+gridstart)/7)*23-2)
			else:
				xticks.append(i)
			xlabels.append(dt.strftime("%b"))

	# percentage of tasks performed on each day
	day_percents = []
	day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
	for d in day_names:
		day_percents.append(days_stats.get(d, 0)/days_stats["tot"]*100)

	#fig = plt.figure()
	fig, axes = plt.subplots(2, 1)
	if use_gridplot:
		axes[0].imshow(gridplot)
	else:
		axes[0].plot(range(len(ma)), ma)
	axes[1].bar(range(7), day_percents)
	plt.sca(axes[0])
	plt.title("%d-Task Weighted Moving Average" % WMA_INT)
	plt.xticks(xticks, xlabels)
	if use_gridplot:
		plt.yticks([], [])
	else:
		plt.grid(True, "major", "x", linestyle="--", linewidth=1)
	plt.sca(axes[1])
	plt.title("Distribution of Time Spent on Tasks")
	plt.ylabel("%")
	plt.xticks(range(7), [d[:3] for d in day_names])

	fig.tight_layout()
	return fig, getStatsAvgBreakdown(task_stats), gridplot

def genGridPlot(productivity=[]):
	sq_size = 20
	spacing = 3
	grid_size = sq_size + spacing
	width = (sq_size+spacing)*52-spacing
	height = (sq_size+spacing)*7-spacing
	img = Image.new("RGB", (width, height+sq_size), (255, 255, 255))
	px = img.load()
	font = ImageFont.truetype("UbuntuMono-R.ttf", 16)

	x = 0
	y = 0
	day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
	
	#extra_days = first_day_idx + (6-last_day_idx)
	#if (len(productivity)+extra_days) > 364:
	#	productivity = productivity[-365+extra_days:]

	first_day = time.strftime("%A", time.localtime(productivity[0][0]))
	y = day_names.index(first_day) * grid_size
	
	for p in productivity:
		color = colorFromNormScore(p[1])
		for j in range(y, y+sq_size):
			for i in range(x, x+sq_size):
				px[i, j] = color

		dt = datetime.fromtimestamp(p[0])# + timedelta(days=1)
		if dt.day == 1:
			diff = int((spacing+1)/2)
			tempx = max(0, x-diff)
			tempy = max(0, y-diff)
			if tempx:
				for j in range(tempy, height):
					px[tempx, j] = (0, 0, 0)
			if tempy:
				xlim = int(x+sq_size+diff)
				for i in range(tempx, xlim):
					px[i, tempy] = (0, 0, 0)
				for j in range(0, tempy):
					px[xlim-1, j] = (0, 0, 0)
			ImageDraw.Draw(img).text((x, height+spacing), dt.strftime("%b"), (0, 0, 0), font=font)
		y += grid_size
		if y >= height:
			y = 0
			x += grid_size

	return img, day_names.index(first_day)

def getStatsAvgBreakdown(task_stats=None, sorting=0):
	task_data = readData()
	if task_stats == None:
		data = readStats()
		productivity, days_stats, task_stats = processStatsData(data, task_data)
	# create javascript-friendly dict (to be read as JSON)
	avg_stats = []
	hdrs = ["Task", "Avg Score", "Most Frequent Day", "Avg Frequency"]
	task_names = sorted(task_stats.keys())	# order alphabetically
	for t in task_names:
		if t not in task_data or not task_data[t]["isActive"]: continue
		avgscore = task_stats[t]["score"] / task_stats[t]["completed"]
		top_day = max(set(task_stats[t]["days"]), key=task_stats[t]["days"].count)
		day_ratio = task_stats[t]["days"].count(top_day) / len(task_stats[t]["days"]) * 100
		top_day += " (%d%%)" % day_ratio
		avg_freq = secToTimeString(avgscore * task_stats[t]["freq"])
		avg_stats.append({hdrs[0]:t,
						hdrs[1]:round(avgscore,2),
						hdrs[2]:top_day,
						hdrs[3]:avg_freq})
	avg_stats = sorted(avg_stats, key=lambda x: x[hdrs[sorting]])	# sort by score
	return {"Headers": hdrs, "Stats": avg_stats}

def colorFromNormScore(score, colorType="RGB"):
	
	if score < 80:
		r = 224
		g = int(224 * (score/80))
		b = 0
	else:
		r = int(224 -  224 * (score-80)/20)
		g = 224
		b = 0

	if colorType.lower() == "hex":
		return "#%0.2X%0.2X%0.2x" % (r, g, b)
	
	return (r, g, b)

def secToTimeString(t, whole=False):
	# only converts to days or months
	days = t / 86400
	if whole:
		days = int(days + 0.5)
		if days < 0:
			timestr = "Overdue"
		elif days < 1:
			timestr = "Today"
		elif days < 2:
			timestr = "1 day"
		elif days < 7:
			timestr = "%d days" % days
		elif days <= 28:
			timestr = "%d wks" % (days/7+0.5)
		else:
			timestr = "%d mon" % (days/30+0.5)
	else:
		if days < 14:
			timestr = "%dd" % days
		elif days <= 28:
			timestr = "%dw" % (days / 7 + 0.5)
		else:
			timestr = "%dM" % (days / 30 + 0.5)
	return timestr

if __name__ == "__main__":
	print("Not intended to be run as main program")
