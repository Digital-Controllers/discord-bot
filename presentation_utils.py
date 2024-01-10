"""Contains utility functions for communication/presenting text to users"""


def get_ord(n: int) -> str:
	suffixes = ("th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th")
	if n % 100 > 13:
		return suffixes[n % 10]
	else:
		return suffixes[n % 100]
