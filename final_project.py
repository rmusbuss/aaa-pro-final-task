#!/usr/bin/env python

"""
Bot for playing tic tac toe game with multiple CallbackQueryHandlers.
"""
from copy import deepcopy
import logging
import numpy as np
from asyncio import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)
import os
import itertools


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
# set higher logging level for httpx to avoid all
# GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# get token using BotFather
TOKEN = os.getenv("TG_TOKEN")

CONTINUE_GAME, FINISH_GAME = range(2)

FREE_SPACE = "."
CROSS = "X"
ZERO = "O"


DEFAULT_STATE = [[FREE_SPACE for _ in range(3)] for _ in range(3)]


def get_default_state():
    """Helper function to get default state of the game"""
    return deepcopy(DEFAULT_STATE)


def generate_keyboard(state:
                      list[list[str]]) -> list[list[InlineKeyboardButton]]:
    """Generate tic tac toe keyboard 3x3 (telegram buttons)"""
    return [
        [InlineKeyboardButton(state[r][c],
                              callback_data=f"{r}{c}") for r in range(3)]
        for c in range(3)
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    context.user_data["keyboard_state"] = get_default_state()
    reply_markup = create_inline_markup(context.user_data["keyboard_state"])
    await update.message.reply_text(
        f"X (your) turn! Please, put X to the free place",
        reply_markup=reply_markup
    )
    return CONTINUE_GAME


async def make_AI_turn(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logic for AI turns"""
    query = update.callback_query
    # keyboard state
    current_keyboard_setup = np.array(context.user_data["keyboard_state"])
    # obtaining empty cells
    possible_rs, possible_cs = np.where(current_keyboard_setup == ".")
    # randomly chosing one of the cells
    cell_to_go = np.random.randint(len(possible_rs))
    random_c, random_r = possible_rs[cell_to_go], possible_cs[cell_to_go]
    # putting zero there
    current_keyboard_setup[random_c][random_r] = ZERO
    # setting the keyboard state via new setup
    context.user_data["keyboard_state"] = list(current_keyboard_setup)
    reply_markup = create_inline_markup(current_keyboard_setup)
    # notifying user that bot made its move and showing markup
    await query.edit_message_text(
        text="O (AI) turn resulted at:", reply_markup=reply_markup
    )


def check_winner(field: list[str]) -> (str, int):
    """checking current field situation. Is there a winner?"""
    # crosses? Zeroes? Or no one?
    winner = won(field)

    if winner in ["X", "O"]:
        # crosses or zeroes?
        return FINISH_GAME, f"WOW! {winner} is winner!"
    else:
        # tie or continue the game?
        if "." not in list(itertools.chain.from_iterable(field)):
            return FINISH_GAME, "It is a TIE :( No one wins"
        return CONTINUE_GAME, ""


def create_inline_markup(field: list[str]) -> InlineKeyboardMarkup:
    """generates inline keyboard markup of current keyboard field"""
    keyboard = generate_keyboard(field)
    return InlineKeyboardMarkup(keyboard)


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main processing of the game. Returns game statuses, whether it is time
    to finish game or continue it"""
    query = update.callback_query
    await query.answer()

    r, c = map(int, query.data)
    # keyboard state
    new_keyboard = context.user_data["keyboard_state"]

    # checking whether the cell is already occupied by one of the markers
    if new_keyboard[r][c] != ".":
        reply_markup = create_inline_markup(new_keyboard)

        # To address the API error: message cannot be edited to same message
        if query.message.text != f"You cannot place markers on occupied cells":
            await query.edit_message_text(
                text=f"You cannot place markers on occupied cells",
                reply_markup=reply_markup,
            )
        return CONTINUE_GAME
    # putting cross to the picked cell by user
    new_keyboard[r][c] = CROSS
    reply_markup = create_inline_markup(new_keyboard)
    await query.edit_message_text(
        text="X (your) turn resulted at:", reply_markup=reply_markup
    )

    # sleep so that user could read what bot writes
    await sleep(1)

    # obtaining data for current game situation (user wins or not?)
    game_status, reply_message = \
        check_winner(context.user_data["keyboard_state"])
    if game_status == CONTINUE_GAME:
        # User doesn't win. AI turn now
        await make_AI_turn(update, context)
        # check whether AI wins
        game_status, reply_message = \
            check_winner(context.user_data["keyboard_state"])
        if game_status == CONTINUE_GAME:
            # AI doesn't win
            return CONTINUE_GAME
        else:
            # AI wins! Congratulations!
            reply_markup = \
                create_inline_markup(context.user_data["keyboard_state"])
            await query.edit_message_text(text=reply_message,
                                          reply_markup=reply_markup)
            return FINISH_GAME
    else:
        # User wins. Congratulations!
        await query.edit_message_text(text=reply_message,
                                      reply_markup=reply_markup)
        return FINISH_GAME


def won(field: list[str]) -> str:
    """Check if crosses or zeros have won the game"""
    # Check rows and columns
    for i in range(3):
        if field[i][0] == field[i][1] == field[i][2] and \
                field[i][0] in ["X", "O"]:
            # Winner on ith row
            return field[i][0]
        if field[0][i] == field[1][i] == field[2][i] and \
                field[0][i] in ["X", "O"]:
            # Winner on ith column
            return field[0][i]

    # Check diagonals
    if field[0][0] == field[1][1] == field[2][2] and field[0][0] in ["X", "O"]:
        # Winner on main diagonal
        return field[0][0]
    if field[0][2] == field[1][1] == field[2][0] and field[0][2] in ["X", "O"]:
        #  Winner on secondary diagonal
        return field[0][2]

    # No winner
    return None


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    # reset state to default so you can play again with /start
    context.user_data["keyboard_state"] = get_default_state()
    return ConversationHandler.END


def main() -> None:
    """Run the bot"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Setup conversation handler with the states CONTINUE_GAME and FINISH_GAME
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONTINUE_GAME: [
                CallbackQueryHandler(game, pattern="^" + f"{r}{c}" + "$")
                for r in range(3)
                for c in range(3)
            ],
            FINISH_GAME: [
                CallbackQueryHandler(end, pattern="^" + f"{r}{c}" + "$")
                for r in range(3)
                for c in range(3)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add ConversationHandler to application that
    # will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
