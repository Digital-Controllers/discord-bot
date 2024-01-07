from discord import app_commands, Interaction
from tb_discord.tb_ui.lesson_tracking import Requests
from tb_db import sql_op


__all__ = ["command_list"]


@app_commands.command()
async def register(inter: Interaction):
	if sql_op("SELECT COUNT(1) FROM students WHERE uid = %s", (inter.user.id,)) == (0,):
		sql_op("INSERT INTO students VALUES (%s, default, default, default)", (inter.user.id,))
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
	# a two byte big-endian unsigned integer. Ex. ACAD-02 is stored in bytes 2 & 3
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

command_list = [lesson_requests, register, request_training]
