import telegram
import logging
import os
import yagmail


def send_message(message, test_mode, race=None):
    logging.info('Sending Telegram message - {}'.format(message))
    token = os.environ['TELEGRAM_BOT']
    bot = telegram.Bot(token=token)
    message = message.replace('*', '')

    if test_mode:
        bot.send_message(chat_id='-1001365813396',
                         text=message,
                         parse_mode=telegram.ParseMode.MARKDOWN)  # Monitor Test
    else:
        if race == 'Magic':
            bot.send_message(chat_id='-1001459804346',
                             text=message,
                             parse_mode=telegram.ParseMode.MARKDOWN)  # Magic Mike Tips
        else:
            bot.send_message(chat_id='-1001229649531',
                             text=message,
                             parse_mode=telegram.ParseMode.MARKDOWN)  # Greyhound Alerts
            if race is not None:
                if ('Central' in race) or ('Hove' in race) or ('Crayford' in race):
                    bot.send_message(chat_id='-1001299965928',
                                     text=message,
                                     parse_mode=telegram.ParseMode.MARKDOWN)  # T&H Alerts


def send_email(message, subject):
    password = os.environ('PWORD')
    yag = yagmail.SMTP('spencer.jago@digital.landregistry.gov.uk', password)
    contents = [message]
    emails = []
    emails.append('spencer.jago@gmail.com')

    yag.send(emails, subject, contents)
