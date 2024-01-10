"""Module containing ui elements intended for use in the lesson_tracking commands"""
from discord import Embed, Thread, ButtonStyle, Interaction, Message
from discord.ui import Button, View
from presentation_utils import get_ord
from tb_db import sql_op


__all__ = ['CohortUI', 'Requests']


class Requests(Embed):
	def __init__(self, atsa_data: list[int], tca_data: list[int]):
		super().__init__(title=f"Current Lesson Requests", color=0x3EBBE7)
		self.set_author(name='Digital Controllers')
		self.set_thumbnail(url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")

		if max(atsa_data) != 0:
			requested_atsa = str(atsa_data.index(max(atsa_data))).zfill(2)
			self.add_field(name="Most Requested ATSA Lesson:", value=f"ACAD-{requested_atsa}")
		else:
			self.add_field(name="Most Requested ATSA Lesson:", value=f"No requested ATSA lessons")

		if max(tca_data) != 0:
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


class CohortUI(View):
	@classmethod
	async def create(cls, msg: Message, thread: Thread, branch: int, num: int):
		return await msg.edit(view=CohortUI(thread, branch, num))

	@classmethod
	async def find(cls, msg: Message, thread: Thread, view_data):
		view_data = int(view_data)
		branch = view_data >> 16
		num = view_data & 0x1111
		return await msg.edit(view=CohortUI(thread, branch, num))

	def __init__(self, thread: Thread, branch: int, num: int):
		super().__init__()
		self.thread = thread
		self.branch = branch
		self.num = num
		self.add_item(CohortJoinButton(branch, num))
		self.add_item(CohortLeaveButton(thread, branch, num))


class CohortJoinButton(Button):
	def __init__(self, branch: int, num: int):
		super().__init__(style=ButtonStyle.primary, label="Join Cohort")
		self.branch = branch
		self.num = num

	async def callback(self, inter: Interaction):
		existing_cohorts = sql_op("SELECT cohort FROM students WHERE uid = %s", (inter.user.id,))[0]

		if (existing_cohorts >> (self.branch * 16)) & 0x0000ffff != 0:
			await inter.response.send_message("You are already in a cohort, please leave that one before trying to join a new one.",
				ephemeral=True)
		else:
			await inter.response.send_message(f"Welcome to the {self.num}{get_ord(self.num)} {'ATSA' if self.branch == 0 else 'TCA'} "
				f"Cohort <@{inter.user.id}>", ephemeral=True)
			existing_cohorts |= self.num << (self.branch * 16)
			sql_op("UPDATE students SET cohort = %s WHERE uid = %s", (existing_cohorts, inter.user.id))


class CohortLeaveButton(Button):
	def __init__(self, thread, branch: int, num: int):
		super().__init__(style=ButtonStyle.primary, label="Leave Cohort")
		self.thread = thread
		self.branch = branch
		self.num = num

	async def callback(self, inter: Interaction):
		existing_cohorts = sql_op("SELECT cohort FROM students WHERE uid = %s", (inter.user.id,))[0]
		if (existing_cohorts >> (self.branch * 16)) & 0x0000ffff != self.num:
			await inter.response.send_message("You do not belong to this cohort", ephemeral=True)
		else:
			existing_cohorts &= ~(0xffff << (self.branch * 16))
			await self.thread.remove_user(inter.user)
			await inter.response.defer(ephemeral=True)
			sql_op("UPDATE students SET cohort = %s WHERE uid = %s", (existing_cohorts, inter.user.id))



