from math import *
import time

g_lat = 28.385
g_lon = -81.564
tz_offset = -4 if time.localtime().tm_isdst else -5# timezone (UTC difference)
window_angle = 288 # angle in degrees of a window, clockwise from North (0 or 360)
g_min_elev = 10
g_max_elev = 36

def getSunAngle(year, month, day, hour, minute, lat, lon):
    # magic numbers EVERYWHERE
    # all (except one - julian_day) formulas obtained from the National Oceanic & Atmospheric Administration (NOAA)
    # calculations spreadsheet "NOAA_Solar_Calculations_day.xls" available at https://www.esrl.noaa.gov/gmd/grad/solcalc/calcdetails.html
    # The letter comment above each calculation corresponds to the column of the above spreadsheet
    # julian_day calculation obtained from wikipedia
    
    div1 = int((month-14)/12) # random snippit used several times in the julian_day calculation
    julian_day = (1461 * (year + 4800 + div1))/4 + (367 * (month - 2 - 12 * (div1)))/12 - (3 * int(int((year + 4900 + div1)/100))/4) + day - 32075 + (hour-tz_offset-12)/24 + minute/1440

    #G
    julian_century = (julian_day-2451545)/36525

    #I
    mean_long_sun = (280.46646 + julian_century * (36000.76983 + julian_century * 0.0003032)) % 360

    #J
    mean_anom_sun = 357.52911 + julian_century * (35999.05029 - 0.0001537*julian_century)

    #K
    earth_orbit = 0.016708634 - julian_century*(0.000042037 + 0.0000001267 * julian_century)

    #L
    sun_eq_ctr = sin(radians(mean_anom_sun)) * (1.914602-julian_century*(0.004817+0.000014*julian_century)) + sin(radians(2*mean_anom_sun))*(0.019993-0.000101*julian_century) + sin(radians(3*mean_anom_sun)) * 0.000289

    #M
    sun_true_long = mean_long_sun + sun_eq_ctr

    #P
    sun_app_long = sun_true_long - 0.00569 - 0.00478 * sin(radians(125.04-1934.136 * julian_century))

    #Q
    mean_obliq_eclip = 23+(26+((21.448-julian_century*(46.815+julian_century*(0.00059-julian_century*0.001813))))/60)/60

    #R
    obliq_corr = mean_obliq_eclip + 0.00256 * cos(radians(125.04-1934.136 * julian_century))

    #T
    sun_declin = degrees(asin(sin(radians(obliq_corr))*sin(radians(sun_app_long))))

    #U
    var_y = tan(radians(obliq_corr/2))**2

    #V
    eq_time = 4 * degrees(var_y*sin(2*radians(mean_long_sun))-2*earth_orbit*sin(radians(mean_anom_sun))+4*earth_orbit*var_y*sin(radians(mean_anom_sun))*cos(2*radians(mean_long_sun))-0.5*var_y**2*sin(4*radians(mean_long_sun)) - 1.25*earth_orbit**2*sin(2*radians(mean_anom_sun)))

    #AB
    true_solar_time = ((hour/24 + minute/1440)*1440 + eq_time + 4*lon - 60*tz_offset) % 1440

    #AC
    hour_angle = true_solar_time/4+180 if (true_solar_time/4)<0 else true_solar_time/4-180

    #AD
    solar_zenith_angle = degrees(acos(sin(radians(lat))*sin(radians(sun_declin))+cos(radians(lat))*cos(radians(sun_declin))*cos(radians(hour_angle))))

    #AE
    solar_elev_angle = 90-solar_zenith_angle

    #AF
    atm_refrac = 0
    if solar_elev_angle <= 85:
        if solar_elev_angle > 5:
            atm_refrac = 58.1/tan(radians(solar_elev_angle))-0.07 / (tan(radians(solar_elev_angle)))**3 + 0.000086 / (tan(radians(solar_elev_angle)))**5
        elif solar_elev_angle > -0.575:
            atm_refrac = 1735 + solar_elev_angle*(-518.2 + solar_elev_angle*(103.4 + solar_elev_angle*(-12.79 + solar_elev_angle*0.711)))
        else:
            atm_refrac = -20.772/tan(radians(solar_elev_angle))/3600

    #AG
    corrected_solar_elev = solar_elev_angle + atm_refrac # angle between sun and horizon (0 means at horizon, negative means below horizon - sun has set)
    
    #AH
    solar_azimuth_angle = degrees(acos(((sin(radians(lat))*cos(radians(solar_zenith_angle)))-sin(radians(sun_declin)))/(cos(radians(lat))*sin(radians(solar_zenith_angle)))))
    if hour_angle>0:
        solar_azimuth_angle = (solar_azimuth_angle + 180) % 360
    else:
        solar_azimuth_angle = (540 - solar_azimuth_angle) % 360
        
    if corrected_solar_elev <= 0: return 0, 0 # sun is below horizon, so don't care about position
    return solar_azimuth_angle, solar_elev_angle

def getSunlightTimes(lat, lon, angle, lower_lim_adjust, upper_lim_adjust, min_elev=0, max_elev=90):
    lower_lim = angle - lower_lim_adjust # adjustments for obstructions to window
    upper_lim = angle + upper_lim_adjust

    # current data
    today = time.strftime("%d_%m_%Y_%H_%M", time.localtime(time.time()))
    today = today.split('_')
    day = int(today[0])
    month = int(today[1])
    year = int(today[2])
    hour = 0 #int(today[3])
    minute = 0 #int(today[4])

    # start at midnight, increase time by 1 minute each loop to find when sunlight
    # is expected to first enters window and when near-direct sunlight starts
    azimuth, elev = getSunAngle(year, month, day, hour, minute, lat, lon)
    while azimuth < lower_lim or elev > max_elev:
        minute += 1
        if minute >= 60:
            minute = 0
            hour += 1
        azimuth, elev = getSunAngle(year, month, day, hour, minute, lat, lon)
    nearDirectStart = "%02d:%02d" % (hour, minute)

    prev_elev = 0
    while elev > prev_elev:
        minute += 1
        if minute >= 60:
            minute = 0
            hour += 1
        prev_elev = elev
        azimuth, elev = getSunAngle(year, month, day, hour, minute, lat, lon)

    # find upper limit of "near-direct" sunlight
    while azimuth < upper_lim and azimuth != 0 and elev > min_elev:
        minute += 1
        if minute >= 60:
            minute = 0
            hour += 1
        azimuth, elev = getSunAngle(year, month, day, hour, minute, lat, lon)
    nearDirectEnd = "%02d:%02d" % (hour, minute)

    return nearDirectStart, nearDirectEnd

if __name__ == "__main__":
    lower_lim = window_angle - 65 # adjustments for obstructions to window
    upper_lim = window_angle + 65

    # current data
    today = time.strftime("%d_%m_%Y_%H_%M", time.localtime(time.time()))
    today = today.split('_')
    day = int(today[0])
    month = int(today[1])
    year = int(today[2])
    hour = int(today[3])
    minute = int(today[4])
    strTime = "%02d:%02d" % (hour, minute)
    azimuth, elev = getSunAngle(year, month, day, hour, minute, g_lat, g_lon)
    print("It is %s, Sun azimuth is currently %.2f deg (%.2f deg from horizon)" % (strTime, azimuth, elev))

    # find time with "near-direct" sunlight
    light_start = ""    # sunlight first enters window (at quite an angle)
    hour = 0
    minute = 0

    # start at midnight, increase time by 1 minute each loop to find when sunlight
    # is expected to first enters window and when near-direct sunlight starts
    azimuth, elev = getSunAngle(year, month, day, hour, minute, g_lat, g_lon)
    while azimuth < lower_lim or elev > g_max_elev:
        minute += 1
        if minute >= 60:
            minute = 0
            hour += 1
        azimuth, elev = getSunAngle(year, month, day, hour, minute, g_lat, g_lon)
        if light_start == "" and azimuth > window_angle - 90 + 9:
            light_start = "%02d:%02d" % (hour, minute)
            print("Sunlight will first enter window at %s" % light_start)
    nearDirectStart = "%02d:%02d" % (hour, minute)

    # find upper limit of "near-direct" sunlight
    while azimuth < upper_lim and azimuth != 0 and elev > g_min_elev: # azimuth = 0 means sun has set
        minute += 1
        if minute >= 60:
            minute = 0
            hour += 1
        azimuth, elev = getSunAngle(year, month, day, hour, minute, g_lat, g_lon)
    nearDirectEnd = "%02d:%02d" % (hour, minute)
    
    print("Sun will give near-direct light from %s to %s" % (nearDirectStart, nearDirectEnd))
    
