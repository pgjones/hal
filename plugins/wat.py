__commands__ = '''
	wat - provides link to random WAT image
'''

import requests

def plugin(bot):
	@bot.hear('wat$')
	def wat(response):
		r = requests.get('http://watme.herokuapp.com/random')
		return r.json()['wat']
