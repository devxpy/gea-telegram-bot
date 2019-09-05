import djclick as click
from telebot.bot import start_bot


@click.command()
def command():
    start_bot()
