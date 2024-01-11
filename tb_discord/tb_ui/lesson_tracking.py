"""Module containing ui elements intended for use in the lesson_tracking commands"""
from discord import Embed, Message, TextChannel
from discord.abc import GuildChannel
from discord.errors import NotFound
from discord.ext import tasks
from tb_db import sql_op
from time import time
import logging
import server_data


class Requests(Embed):
	def __init__(self, atsa_data: list[int], tca_data: list[int]):
		super().__init__(title=f"Current Lesson Requests", color=0x3EBBE7)
		self.set_author(name='Digital Controllers')
		self.set_thumbnail(url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")

		if (atsa_max := max(atsa_data)) != 0:
			requested_atsa = str(atsa_data.index(max(atsa_data))).zfill(2)
			self.add_field(name="Most Requested ATSA Lesson:", value=f"ACAD-{requested_atsa}")
		else:
			self.add_field(name="Most Requested ATSA Lesson:", value=f"No requested ATSA lessons")

		if (tca_max := max(tca_data)) != 0:
			requested_tca = str(tca_data.index(max(tca_data))).zfill(2)
			self.add_field(name="Most Requested TCA Lesson:", value=f"TACAD-{requested_tca}")
		else:
			self.add_field(name="Most Requested TCA Lesson:", value=f"No requested TCA lessons")

		top_requested = []
		for _ in range(5):
			atsa_max = max(atsa_data)
			tca_max = max(tca_data)
			if atsa_max > tca_max:
				top_requested.append(f"ACAD-{str(atsa_data.index(atsa_max)).zfill(2)}")
				atsa_data[atsa_data.index(atsa_max)] = 0
			else:
				if tca_max == 0:
					top_requested.append("No further requests")
				else:
					top_requested.append(f"TACAD-{str(tca_data.index(tca_max)).zfill(2)}")
					tca_data[tca_data.index(tca_max)] = 0

		self.add_field(name="Top 5 Requested Lessons:", value="\n".join(top_requested), inline=False)
