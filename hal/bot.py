# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import re

from injector import inject

from hal.listeners import TextListener
from hal.plugin import PluginModuleCollector

class Bot(object):
	def __init__(self, name):
		self.name = name

	def run(self):
		self._reload_plugins()
		self.adapter.run()
		
	@inject(plugin_module_collector = PluginModuleCollector)
	def _reload_plugins(self, plugin_module_collector):
		self._listeners = []
		self._commands_help = []
		modules = plugin_module_collector.collect()
		for m in modules:
			m.plugin(self)
			try:
				commands = [c.strip() for c in m.__commands__.splitlines() if c.strip()]
				self._commands_help.extend(commands)
			except AttributeError:
				pass

		self._commands_help.sort()

	def hear(self, regexp, callback = None):
		if callback is None:
			def decorator(function):
				self.hear(regexp, function)
				return function
			return decorator
		else:
			self._listeners.append(TextListener(self, self._regexp_object(regexp), callback))

	def respond(self, regexp, callback = None):
		if callback is None:
			def decorator(function):
				self.respond(regexp, function)
				return function
			return decorator
		else:
			pattern, flags = self._regexp_pattern_and_flags(regexp)
			assert not pattern.startswith('^')

			new_regexp = re.compile(r'^%s[:,]?\s*(?:%s)' % (self.name, pattern,), flags)
			self._listeners.append(TextListener(self, new_regexp, callback))

	def _regexp_object(self, regexp):
		if not hasattr(regexp, 'match'):
			regexp = re.compile(regexp, re.IGNORECASE)

		return regexp

	def _regexp_pattern_and_flags(self, regexp):
		if hasattr(regexp, 'match'):
			pattern, flags = regexp.pattern, regexp.flags
		else:
			pattern, flags = regexp, re.IGNORECASE

		return pattern, flags

	def receive(self, message):
		for listener in self._listeners:
			listener(message)

	def send(self, envelope, message):
		self.adapter.send(envelope, message)

	def reply(self, envelope, message):
		self.adapter.reply(envelope, message)

	@property
	def commands_help(self):
		return self._commands_help
