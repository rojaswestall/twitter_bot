# author: Gabe Rojas-Westall (github: rojaswestall)

import tweepy
from datetime import datetime
from json import loads
from requests import get
from mgconfig import *
from threading import Thread
from time import sleep
from message_format import time_message, inc_or_dec


# Authenticating with Tweepy
auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)


# The URL is a link to the json object of the price of a currency in terms of another specified currency
# Here, the json objects will have the price in USD because syms=USD
# Add the coin code in all CAPS to coins for the coins you want to be monitored
# The max it can do is 4 or 5 coins because of the character limit on tweets
coins = ['BTC', 'ETH', 'LTC', 'XRP', 'SC']
coin_list = []

for code in coins:
	coin = (code, 'https://min-api.cryptocompare.com/data/price?fsym=' + code + '&tsyms=USD')
	coin_list.append(coin)


# Returns the price for any coin given as an arugment.
# Returns in this format: {'USD': 2764} (dictionary)
def coin_price(coin): 
	price = loads(get(coin[1]).text) 
	return price


# Simple %Change calculator
def percent_change(original, new):
	percentchange = (abs(original - new) / original) * 100
	return percentchange


# A proportion checker that returns true if the percent change/hour is greater than 5%
def proportion_check(old_price, new_price, ogtime, now):
	percent = percent_change(old_price, new_price)
	timedif = now - ogtime
	if timedif.seconds == 0:
		return False
	elif (percent / timedif.seconds) >= (5/3600): # 3600 sec = 1 hour
		return True
	return False


# A function that monitors the price fluctuation of a coin and tweets if there is a certain 
# percent change. 
def change_monitor(coin):
	print('Monitor started for ' + coin[0])
	ogtime = datetime.now()
	old_price = coin_price(coin)['USD']
	new_price = old_price

	# Check if price change is greater than the specified %. 
	# If it's not, wait a minute, update the new prices, and try again
	while percent_change(old_price, new_price) < 5: # not proportion_check(old_price, new_price, ogtime, datetime.now())
		sleep(60)
		new_price = coin_price(coin)['USD']
		# Reset the price of the coin every 12 hours
		timedif = datetime.now() - ogtime
		if timedif.seconds >= 43200:
			ogtime = datetime.now()
			old_price = new_price

	# If it's greater, tweet the change, whether it increased or decreased, and the period of time it took
	recordtime = datetime.now()
	timedif = recordtime - ogtime
	hours = int(timedif.seconds / 3600) # The number of hours (-minutes) it took to change 5%
	minutes = int((timedif.seconds - (hours * 3600)) / 60) # The number of minutes (-hours) it took to change 5%

	# Making the tweet look pretty :)
	change = inc_or_dec(new_price, old_price)
	hours, minutes, hourmsg, minutemsg = time_message(hours, minutes)
	
	# Tweet it!
	message = '{} {} {:04.2f}{} in the past {}{}{}{}!\n\nThe new price is ${}'.format(coin[0], change, percent_change(old_price, new_price), '%', str(hours), hourmsg, str(minutes), minutemsg, str(new_price))
	api.update_status(message)
	print('Price change tweeted for ' + coin[0])

	# Restart
	change_monitor(coin)


# Tweets the price of all desired coins every 12 hours
def price_tweet(coin_list, old_price_list):
	global first
	rightnow = datetime.now().strftime("%b. %d, %I:%M%p")
	message = 'Crypto prices ({}):\n'.format(rightnow)
	new_price_list = []
	for i in range(0, len(coin_list)):
		coin = coin_list[i]
		price = coin_price(coin)['USD']
		# Adding the price to a list to use for the next time price_tweet is called
		new_price_list.append(price)

		# If this is the first time running the function set the old price and new price to be the same
		if first == True:
			old_price_list[i] = price

		change = round(percent_change(old_price_list[i], price), 1)

		# Setting the right up or down symbol next to percent change
		if change == 0.0:
			updown = '\u27a4' # Right Symbol
		elif price > old_price_list[i]:
			updown = '\u25b2' # Up Symbol
		elif price == old_price_list[i]:
			updown = '\u27a4' # Right Symbol
		else:
			updown = '\u25bc' # Down Symbol

		message = message + '\n{}{}{} {}: ${}'.format(updown, change, '%', coin[0], str(price))

	#Tweet the prices
	api.update_status(message)
	print('Prices for all coins tweeted')

	# No longer in the first iteration of the loop
	first = False

	# Sleep for 12 hours. 43200
	sleep(43200) 

	# Restart
	price_tweet(coin_list, new_price_list)

	# coin[0] will print out the cyrptocurrency code for that coin: 'BTC'
	# price['USD'] will give the dictionary price value for BTC if price = coin_price(btc)


# The function that will start the monitoring of all specified coins
def monitor_coins(coin_list):
	# Start tweeting the price every 12 hours
	thread = Thread(target = price_tweet, args = (coin_list, dummylist))
	thread.start()
	# Start monitoring each coin
	for coin in coin_list:
		thread = Thread(target = change_monitor, args = (coin,))
		thread.start()
	
dummylist = []
for i in range(0, len(coin_list)): 
	dummylist.append(0)
first = True
monitor_coins(coin_list)



