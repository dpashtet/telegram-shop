import SimpleQIWI, telebot, time, shelve, requests
import dop, config, files
from coinbase.wallet.client import Client

bot = telebot.TeleBot(config.token)

he_client = []

def creat_bill_qiwi(chat_id, callback_id, message_id, sum, name_good, amount):
	#if dop.amount_of_goods(name_good) <= int(amount): bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Выберите меньшее число товаров к покупке')
	#el
	if dop.payments_checkvkl() == None: bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Принять деньги на киви кошелёк в данный момент невозможно!')
	else:
		phone, token = dop.get_qiwidata()
		api = SimpleQIWI.QApi(token=token, phone=phone)
		comm = 'bill|' + dop.generator_pw(10) + '|'
		with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:
			f.write(str(phone) + '\n')
			f.write(token + '\n')
			f.write(str(amount)+ '\n')
			f.write(str(sum)+ '\n')
			f.write(comm)
		key = telebot.types.InlineKeyboardMarkup()
		rurl = 'https://qiwi.com/payment/form/99?extra%5B%27account%27%5D=' + str(phone) + '&amountInteger=' + str(sum) + '&amountFraction=0&extra%5B%27comment%27%5D=' + comm +'&currency=643&blocked[0]=account&blocked[1]=sum&blocked[2]=comment'
		url_button = telebot.types.InlineKeyboardButton("Оплатить в браузере",  rurl)
		b1 = telebot.types.InlineKeyboardButton(text='Проверить оплату', callback_data='Проверить оплату')
		key.add(b1, url_button)
		key.add(telebot.types.InlineKeyboardButton(text = 'Вернуться в начало', callback_data = 'Вернуться в начало'))
		try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='Чтобы купить ' + name_good + ' количеством ' + str(amount) + '\nНадо пополнить qiwi кошелек `' + str(phone) + '` на сумму `' + str(sum) + '` *₽*\nПри переводе обязательно укажите комментарий\n `' + comm + '`\nБез него платёж не зачислится.', parse_mode='Markdown', reply_markup = key)
		#bot.send_message(message.chat.id, '`' + comm + '`', parse_mode='Markdown', reply_markup=key)
		#bot.send_message(chat_id, '`' + comm + '`')
		except: pass
		he_client.append(chat_id)

def check_oplata_qiwi(chat_id, username, callback_id, first_name):
	if chat_id in he_client:
		with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f: name_good = f.read()
		phone = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 0)
		token = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 1)
		amount = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 2)
		price = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 3)
		comm = dop.read_my_line('data/Temp/' + str(chat_id) + '.txt', 4)

		api = SimpleQIWI.QApi(phone=phone, token=token)
		comment = api.bill(int(price), comm)
		api.start()
		time.sleep(1)

		try:
			if api.check(comment):
				he_client.remove(chat_id)
				try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='Платёж успешно зачилен!\nСейчас вы получите ваш товар')
				except: pass
				text = ''
				for i in range(int(amount)):
					if dop.get_goodformat(name_good) == 'file':
						bot.send_document(chat_id, dop.get_tovar(name_good))
					elif dop.get_goodformat(name_good) == 'text':
						text += dop.get_tovar(name_good) + '\n'
				if dop.get_goodformat(name_good) == 'text': bot.send_message(chat_id, text)
				if dop.check_message('after_buy') is True:
					with shelve.open(files.bot_message_bd) as bd: after_buy = bd['after_buy']
					after_buy = after_buy.replace('username', username)
					after_buy = after_buy.replace('name', first_name)
					bot.send_message(chat_id, after_buy)
				for admin_id in dop.get_adminlist(): 
					bot.send_message(admin_id, '*Юзер*\nID: `' + str(chat_id) + '`\nUsername: @' + username + '\nКупил *' + name_good + '*\nНа сумму ' + str(price) + ' р', parse_mode='Markdown')

				dop.new_buy(chat_id, username, name_good, amount, price)
				dop.new_buyer(chat_id, username, price)
			else: bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Деньги ещё не были зачислены!')
		except: pass
		api.stop()


def creat_bill_btc(chat_id, callback_id, message_id, sum, name_good, amount):
	#if dop.amount_of_goods(name_good) <= int(amount): bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Выберите меньшее число товаров к покупке')
	#el
	if dop.get_coinbasedata() == None: bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Принять деньги на btc кошелёк в данный момент невозможно!')
	else:
		api_key, api_secret = dop.get_coinbasedata()
		client = Client(api_key, api_secret)
		account_id = client.get_primary_account()['id']
		sum = int(sum) + 10 #прибавляется комиссия в btc
		btc_price = round(float((client.get_buy_price(currency_pair='BTC-RUB')["amount"])))
		print(btc_price)
		sum = float(str(sum / btc_price)[:10]) #сколько сатох нужно юзеру оплатить
		address_for_tranz = client.create_address(account_id)['address'] #получение кошелька для оплты

		with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:
			f.write(str(amount)+ '\n')
			f.write(str(sum)+ '\n')
			f.write(address_for_tranz)
		key = telebot.types.InlineKeyboardMarkup()
		key.add(telebot.types.InlineKeyboardButton(text='Проверить оплату', callback_data='Проверить оплату btc'))
		key.add(telebot.types.InlineKeyboardButton(text = 'Вернуться в начало', callback_data = 'Вернуться в начало'))
		try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='Чтобы купить ' + name_good + ' количеством ' + str(amount) + '\nПереведите `' + str(sum) + '` btc на адрес `' + str(address_for_tranz) + '`', parse_mode='Markdown', reply_markup=key)
		except: pass
		he_client.append(chat_id)


def check_oplata_btc(chat_id, username, callback_id, first_name):
	if chat_id in he_client:
		with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f: name_good = f.read()
		amount = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 0)
		sum = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 1)
		address = dop.read_my_line('data/Temp/' + str(chat_id) + '.txt', 2)

		r = requests.get('https://blockchain.info/q/addressbalance/' + address)
		s = r.text
		if float(s) >= float(sum):
			try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='Платёж успешно зачилен!\nСейчас вы получите ваш товар')
			except: pass
			text = ''
			for i in range(int(amount)):
				if dop.get_goodformat(name_good) == 'file':
					bot.send_document(chat_id, dop.get_tovar(name_good))
				elif dop.get_goodformat(name_good) == 'text':
					text += dop.get_tovar(name_good) + '\n'
			if dop.get_goodformat(name_good) == 'text': bot.send_message(chat_id, text)
			if dop.check_message('after_buy') is True:
				with shelve.open(files.bot_message_bd) as bd: after_buy = bd['after_buy']
				after_buy = after_buy.replace('username', username)
				after_buy = after_buy.replace('name', first_name)
				bot.send_message(chat_id, after_buy)
			for admin_id in dop.get_adminlist(): 
				bot.send_message(admin_id, '*Юзер*\nID: `' + str(chat_id) + '`\nUsername: @' + username + '\nКупил *' + name_good + '*\nНа сумму ' + str(sum) + ' btc', parse_mode='Markdown')
            #*/
			# dop.new_buy(chat_id, username, name_good, amount, price)
			# dop.new_buyer(chat_id, username, price)
		else: bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Деньги ещё не были зачислены!')









	










