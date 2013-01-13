# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from os import environ

from xmpp import Client, JID, Message, NS_MUC, Presence

from hal.adapter import Adapter as HalAdapter
from hal.messages import TextMessage
from hal.user import User


class JabberConfiguration(object):
	def __init__(self, jid, password, conference_server, rooms):
		self.jid = jid
		self.password = password
		self.rooms = rooms

		jid = JID(jid)
		self.user = jid.getNode()
		self.server = jid.getDomain()

		self.conference_server = conference_server or 'conference.%s' % (self.server,)

class Adapter(HalAdapter):
	def run(self):
		configuration = JabberConfiguration(
			jid = environ['HAL_JABBER_JID'],
			password = environ['HAL_JABBER_PASSWORD'],
			rooms = environ['HAL_JABBER_ROOMS'].split(','),
			conference_server = environ.get('HAL_JABBER_CONFERENCE_SERVER'),
		)
		self.configuration = configuration

		self.connection = connection = self.create_connection(configuration)
		self.connect_to_rooms(connection, configuration)
		connection.RegisterHandler('message', self.handle_message)
		connection.sendInitPresence()

		while True:
			connection.Process(1)

	def create_connection(self, configuration):
		jid = JID(configuration.jid)
		user, server, password = jid.getNode(), jid.getDomain(), configuration.password

		connection = Client(server)
		connection_result = connection.connect()
		if not connection_result:
			raise Exception('Unable to connect to %s' % (server,))
	
		if connection_result != 'tls':
			raise Exception('No TLS support when connecting to %s' % (server,))

		auth_result = connection.auth(user = user, password = password, resource = user)
		if not auth_result:
			raise Exception('Unable to authenticate %s@%s with %s' % (user, server, '*' * len(password)))

		return connection

	def connect_to_rooms(self, connection, configuration):
		for room in configuration.rooms:
			p = Presence(to = '%s@%s/%s' % (room, configuration.conference_server,
				self.bot.name,))
			p.setTag('x', namespace = NS_MUC).setTagData('password', '')
			p.getTag('x').addChild('history', {'maxchars': '0', 'maxstanzas': '0'})
			connection.send(p)

	def handle_message(self, session, message):
		sender, text = message.getFrom(), message.getBody()

		if text:
			room, name = sender.getNode(), sender.getResource()
			user = User(id = name, name = name, room = room)
			self.receive(TextMessage(user, text))

	def send(self, envelope, text):
		message = Message(to = JID('%s@%s' % (envelope.room, self.configuration.conference_server)),
			body = text, typ = 'groupchat')
		self.connection.send(message)