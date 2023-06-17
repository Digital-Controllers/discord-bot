"""Holds shared data and data structures for tb_discord to prevent import chains"""
from collections import deque
from discord import Message, Role


class RolesMessage:
	"""Shell class for message object with role data attached"""
	def __init__(self, message: Message, roles: list[Role]):
		self.message = message
		self.roles = roles


role_messages: deque[RolesMessage] = deque()
