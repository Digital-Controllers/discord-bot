import pymysql
from configs import configs
from discord import app_commands, Interaction, VoiceChannel, Member
from presentation_utils import get_ord
from tb_discord import bot
from tb_discord.tb_commands.filters import check_is_owner
from tb_discord.tb_ui.lesson_tracking import CohortUI, Requests
from tb_db import sql_func, sql_op


__all__ = ["command_list"]


@app_commands.command()
async def register(inter: Interaction):
	if sql_op("SELECT COUNT(1) FROM students WHERE uid = %s", (inter.user.id,)) == (0,):
		sql_op("INSERT INTO students VALUES (%s, default, default, default, NULL)", (inter.user.id,))
		await inter.response.send_message("Registered successfully", ephemeral=True)
	else:
		await inter.response.send_message("You have already registered with Towerbot. To unregister, please contact a DC Staff member",
										  ephemeral=True)


@app_commands.command()
@app_commands.choices(branch=[
	app_commands.Choice(name="ATSA", value=0),
	app_commands.Choice(name="TCA", value=1)
])
async def request_training(inter: Interaction, branch: int, lesson_num: int):
	if lesson_num < 1:
		await inter.response.send_message("That is not a valid lesson", ephemeral=True)

	database = sql_op("SELECT requests FROM students where uid = %s", (inter.user.id,))
	if database is None:
		await inter.response.send_message("You have not registered with Towerbot, please use /register", ephemeral=True)
		return

	# Handle request in student database
	requests = database[0]
	# Requests are stored in the database as big-endian bits with the msb indicating which branch of the curriculum the lesson
	# belongs to. Ex: ACAD 01: 0000_0001; TACAD 02: 1000_0010
	to_request = ((branch << 7) + int(str(lesson_num).zfill(2))).to_bytes(1, "big", signed=False)
	if to_request in requests:
		await inter.response.send_message("You have already requested this lesson", ephemeral=True)
		return
	requests += to_request

	# Log request in server database for easy counting
	request_count_bytes = sql_op("SELECT data FROM server_data WHERE id = 0", ())[0]
	request_counts = [(request_count_bytes[i] << 8) + request_count_bytes[i + 1] for i in range(0, len(request_count_bytes), 2)]
	request_counts[int.from_bytes(to_request, "big", signed=False)] += 1

	# Request counts are stored in a bytestring indexed by the request number as described above. Request counts themselves are
	# a two byte big-endian unsigned integer. Ex. ACAD-02 is stored in bytes 4 & 5
	request_count_bytes = b"".join(map(lambda x: x.to_bytes(2, "big", signed=False), request_counts))

	await inter.response.send_message(f"Request processed", ephemeral=True)

	# Send sql updates to database
	sql_op("UPDATE server_data SET data = %s WHERE id = 0", (request_count_bytes,))
	sql_op("UPDATE students SET requests = %s WHERE uid = %s", (requests, inter.user.id))


@app_commands.command()
async def lesson_requests(inter: Interaction):
	request_count_bytes = sql_op("SELECT data FROM server_data WHERE id = 0", ())[0]
	request_counts = [(request_count_bytes[i] << 8) + request_count_bytes[i + 1] for i in range(0, len(request_count_bytes), 2)]
	atsa_requests = request_counts[:128]
	tca_requests = request_counts[128:]
	await inter.response.send_message(embed=Requests(atsa_requests, tca_requests))


@app_commands.command()
@app_commands.choices(branch=[
	app_commands.Choice(name="ATSA", value=0),
	app_commands.Choice(name="TCA", value=1)
])
@check_is_owner()
async def create_cohort(inter: Interaction, channel: VoiceChannel, branch: int):
	members = channel.voice_states.keys()
	await inter.response.defer(ephemeral=True, thinking=True)

	cohorts = get_cohorts(members)
	if not cohorts:
		await inter.followup.send("There are no registered users in the voice channel", ephemeral=True)
		return

	filter(lambda x: ((x[1] >> (16 * branch)) & 0x0000ffff) == 0, cohorts)

	await inter.followup.send(f"Creating cohort with {len(cohorts)} members", ephemeral=True)

	cohort_data = int.from_bytes(sql_op("SELECT data FROM server_data WHERE id = 1", ())[0], "big")
	next_cohort = (cohort_data >> (16 * branch)) & 0x0000ffff

	cohort_channel = bot.get_channel(configs.cohort_channels[branch])
	cohort_thread = await cohort_channel.create_thread(invitable=True, name=
					f"{next_cohort}{get_ord(next_cohort)} {'ATSA' if branch == 0 else 'TCA'} Prospective Cohort")

	cohort_message = await cohort_thread.send("<@" + "><@".join([str(x[0]) for x in cohorts]) +
		f"> Welcome to the {next_cohort}{get_ord(next_cohort)} {'ATSA' if branch == 0 else 'TCA'} Prospective Cohort!\n\n"
		"Cohorts are small groups of students who attend Digital Controllers sessions around the same time. We encourage "
		"you to get to know each other, ask each other questions, and attend future sessions together! By creating cohorts "
		"we hope to both ease the difficulty of your learning and create a sense of close community.\n\nTo confirm your "
		"interest in this cohort, press the \"Join Cohort\" button below. Don't worry, nothing's permanent, you can always "
		"click the \"Leave Cohort\" button and be removed from this thread. If you would like to invite friends, just @ them "
		"in this thread and they will be added.\n\nWe wish you the best of luck in your future endeavours here at DC!\n\\- DC "
		"Staff and Moderation Team")

	await CohortUI.create(cohort_message, cohort_thread, branch, next_cohort)

	# REMEMBER TO CONVERT TO BYTES FOR BLOB, I SPENT TWO HOURS DEBUGGING THIS
	new_cohort_data = (((next_cohort + 1) << (16 * branch)) + (cohort_data & (0xffff << (16 * (1 - branch))))) \
		.to_bytes(4, "big", signed=False)

	sql_op("UPDATE server_data SET data = %s WHERE id = 1", (new_cohort_data,))
	sql_op("INSERT INTO persistent_messages VALUES (%s, %s, 2, %s)",
		(cohort_message.id, cohort_thread.id, (branch << 16) + next_cohort))

	await inter.followup.send("Created cohort", ephemeral=True)


@sql_func
def get_cohorts(conn: pymysql.Connection, cursor: pymysql.connections.Cursor, members: tuple[int]) -> list[(int, int)]:
	out = []
	for member in members:
		cursor.execute("SELECT cohort FROM students WHERE uid = %s", (member,))
		cohort = cursor.fetchone()
		if cohort is not None:
			out.append((member, cohort[0]))
	return out


command_list = [create_cohort, lesson_requests, register, request_training]
