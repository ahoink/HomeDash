import requests
import time

def getCurrentWeather(lat, lon, apikey):
	params = {
		"appid":apikey, 
		"units":"imperial",
		"exclude":"minutely,alerts,daily",
		"lat":lat,
		"lon":lon
	}
	res = requests.get(url="https://api.openweathermap.org/data/2.5/onecall", params=params)
	return res.json()

def formatWeatherData(data):
	formatted_data = {}
	formatted_data["temp"] = {"actual": int(data["current"]["temp"] + 0.5),
							"feels": int(data["current"]["feels_like"] + 0.5)}
	formatted_data["humidity"] = data["current"]["humidity"]
	formatted_data["weather"] = data["current"]["weather"][0]["main"]
	formatted_data["wid"] = data["current"]["weather"][0]["id"]
	formatted_data["d_n"] = "night" if data["current"]["weather"][0]["icon"][-1] == "n" else "day"
	formatted_data["hourly"] = []
	for item in data["hourly"][1:7]:
		temp = {}
		temp["temp"] = {"actual": int(item["temp"]+0.5), "feels": int(item["feels_like"]+0.5)}
		temp["humidity"] = item["humidity"]
		temp["weather"] = item["weather"][0]["main"]
		temp["wid"] = item["weather"][0]["id"]
		temp["time"] = time.strftime("%H", time.localtime(item["dt"]))
		temp["d_n"] = "night" if item["weather"][0]["icon"][-1] == "n" else "day"
		formatted_data["hourly"].append(temp)
	return formatted_data

if __name__ == "__main__":
	g_lat = 28.385
	g_lon = -81.564
	data = getCurrentWeather(g_lat, g_lon)
	print("Current weather:")
	print("%dF - %s" % (data["current"]["temp"], data["current"]["weather"][0]["main"]))
