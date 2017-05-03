#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 10:34:44 2017

@author: Trevor Gast
"""
import math
#constants
R = 287.0
g0 = 9.80665
TEMP = 288.15
ATM1 = 101325
DENSITY = 1.225
earthRadius = 6356766.0

layers = [0,11000,20000,32000,47000,51000,71000,84852]
lapseRates = [-0.0065,0,0.001,0.0028,0,-0.0028,-0.002,0]

def lapseRate(alt):
    if (alt < -610):
        return #below sea level
    for i,l in enumerate(layers):
        if l == 0:
            continue # skip the first
        if alt <= l:
            return lapseRates[i-1]
    return 0 #mesopause if above 84852

def getAltRange(alt):
    if (alt < -610):
        return #below sea level
    for i,l in enumerate(layers):
        if l == 0:
            continue # skip the first
        if alt <= l:
            return layers[i-1]
    return 84852 #mesopause if above 84852

## for altimeter predictions
def nextLapseRate(alt):
    if (alt < -610):
        return #below sea level
    for i,l in enumerate(layers):
        if l == 0:
            continue # skip the first
        if alt < l:
            return lapseRates[i-1]
    return 0 #mesopause if above 84852

## for altimeter predictions
def getNextAltRange(alt):
    if (alt < -610):
        return # below sea level
    for l in layers:
        if l == 0:
            continue # skip the first
        if alt < l:
            return l
    if (alt < 90000):
        return 90000 # top of chart
    else:
        return 90001 #for now...

## get the Atmosphere based on altitude (m) and temp offset from standard
## this function is a a wrapper for the recursive calculator.
def getAtmosphere(alt,To): # input is geopotential altitude
    # range check
    if (alt < -610):
        alt = -610; # minimum below sea level... per ISA should go to -5000?
    if (alt > 80000):
        print "*** Warning *** Calculator is NOT accurate above 80000 meters!"
    atm = getStandardAtmosphere(alt,To)
    # take relative values and correct density for temperature offset
    if (atm["rho"] > 0):
        atm["rho"] = atm["rho"]*atm["T"]/(atm["T"]+atm["To"])
    # correct temperature with offset
    atm["T"] = atm["T"] + atm["To"]
    return atm

def getStandardAtmosphere(alt,To):
    # calc for sea level
    if (not alt): #sea level or no altitude entered 0 = false
        return {"alt":0,"T":TEMP,"To":To,"p":ATM1,"rho":DENSITY,"ga":0,"grav":9.80665}

    atm0 = getStandardAtmosphere(getAltRange(alt),To)

    if (lapseRate(alt) != 0):
        T1 = atm0["T"] + lapseRate(alt)*(alt-getAltRange(alt))
        rho1 = atm0["rho"]*(T1/atm0["T"])**(-g0/(lapseRate(alt)*R)-1)
        p1 = atm0["p"]*(T1/atm0["T"])**(-g0/(lapseRate(alt)*R))
    else: # lapseRate = 0
        con = (math.e)**(-g0/(R*atm0["T"])*(alt-getAltRange(alt)))
        T1 = atm0["T"]
        p1 = atm0["p"] * con
        rho1 = atm0["rho"] * con
    
    gAlt = earthRadius*alt/(earthRadius-alt) # geometric altitude (true height above sea level)
    grav = g0*(earthRadius/(earthRadius+gAlt))**2
    return {"alt":alt,"T":T1,"To":To,"p":p1,"rho":rho1,"ga":gAlt,"grav":grav}

## input the pressure or density and get the altitude (altimeter)
def getAltitude(p,rho,To):
    # get the first height, check if it is in the first layer (h0 = 0)
    altR = 0
    h1 = 0
    p0 = ATM1;
    rho0 = DENSITY;
    # adjust rho for temp offset
    # getAtmosphere for all alt and To until find adjusted rho, then use rho with no offset in reverse calculation... cheating!
    guess = -6 #starts at -600 m, increments every 100 m
    lastrho = 0
    #lastAlt = 0 #??
    lastT = 0
    while (rho and guess < 900):
        xatm = getAtmosphere(guess*100.0,To)
        if (xatm["rho"] <= rho):
            # weighted mean
            weight = (xatm["rho"] - rho)/(xatm["rho"] - lastrho)
            meanT = (xatm["T"]*(1-weight)) + (lastT*weight) # reverse adjust the rho for no offset
            rho = rho*meanT/(meanT-To) # get the unadjusted rho for guessing
            #console.log("adjusted" + rho);
            break
        lastT = xatm["T"]
        lastrho = xatm["rho"]
        guess += 1
        
    T0 = TEMP # TEMP+To;
    while (h1 >= altR):
        if (nextLapseRate(altR) != 0 and p):
            T1 = T0*(p/p0)**(R*nextLapseRate(altR)/-g0)
            h1 = (T1 - T0)/nextLapseRate(altR) + altR
        elif (nextLapseRate(altR) != 0 and rho):
            T1 = T0*(rho/rho0)**(1.0/(-g0/(R*nextLapseRate(altR))-1.0))
            h1 = (T1 - T0)/nextLapseRate(altR) + altR
        else: # for isothermal layers
            if (p):
                h1 = (math.log(p/p0)*R*T0/-g0) + altR
            if (rho):
                h1 = (math.log(rho/rho0)*R*T0/-g0) + altR
        # check answer and loop
        altR = getNextAltRange(altR)
        if (altR > 90000):
            return 0 # break out if too high altitude
        # also update p0 and T0
        nextATM = getAtmosphere(altR,0)
        p0 = nextATM["p"]
        rho0 = nextATM["rho"]
        T0 = nextATM["T"]
    return h1



## this is for user interaction
run = True
while run:
    print "--------------------------------------------"
    print "International Standard Atmosphere Calculator"
    print "--------------------------------------------"
    print "What do you want to do?"
    print "1) Enter an altitude in meters"
    print "2) Enter an altitude in feet"
    print "3) Enter an altitude in flight level (FL)"
    print "4) Enter a pressure in Pascals"
    print "5) Enter a density in kg/m³"
    print "6) Convert TAS to IAS"
    print "7) Convert IAS to TAS"
    print "8) Quit"
    choice = input("Your choice: ")
    if choice == 8: #quit the program
        run = False
        break
    elif choice == 4:  # get pressure
        pressure = input("Input pressure (Pascals): ")
        tempoffset = input("Input temperature offset: ")
        altitude = getAltitude(float(pressure),False,tempoffset)
        flightLevel = int(round(altitude/30.48))
        zeros = "" if len(str(flightLevel)) > 2 else "0"
        zeros = "00" if len(str(flightLevel)) == 1 else zeros
        print "You are at FL" + zeros + str(flightLevel)
    elif choice == 5:  # get density
        density = input("Input density (kg/m³): ")
        tempoffset = input("Input temperature offset: ")
        altitude = getAltitude(False,float(density),tempoffset)
        flightLevel = int(round(altitude/30.48))
        zeros = "" if len(str(flightLevel)) > 2 else "0"
        zeros = "00" if len(str(flightLevel)) == 1 else zeros
        print "You are at FL" + zeros + str(flightLevel)
    elif choice == 6: # convert to EAS
        speed = input("Input True Airspeed (m/s): ")
        altitude = input("Input Altitude (m): ")
        tempoffset = input("Input temperature offset: ")
        result = getAtmosphere(altitude,tempoffset)
        EAS = speed*math.sqrt(result["rho"]/1.225)
        print "Your EAS is %s m/s" % EAS
        continue
    elif choice == 7: # convert to TAS
        speed = input("Input Indicated Airspeed (m/s): ")
        altitude = input("Input Altitude (m): ")
        tempoffset = input("Input temperature offset: ")
        result = getAtmosphere(altitude,tempoffset)
        TAS = speed*math.sqrt(1.225/result["rho"])
        print "Your TAS is %s m/s" % TAS
    elif choice == 1 or choice == 2 or choice == 3:
        altitude = input("Input Altitude: ")
        tempoffset = input("Input temperature offset: ")
    else:
        print "Try again!"
        continue
    if choice == 2:
        altitude *= 0.3048
    elif choice == 3:
        altitude *= 30.48
    result = getAtmosphere(altitude,tempoffset)
    print "Altitude: %(meters)s m (%(feet)s ft)" % {"meters":round(result["alt"],2),"feet":round(result["alt"]/0.3048,1)}
    print "Geometric Altitude: %s m" % round(result["ga"],2)
    print "Pressure: %s Pa" % round(result["p"],2)
    print "Density: %s kg/m³" % round(result["rho"],6)
    print "Temperature: %(Kel)s K (%(Cel)s °C)" % {"Kel":round(result["T"],2),"Cel":round(result["T"]-273.15,2)}
