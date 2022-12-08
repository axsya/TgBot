import telebot, wikipedia, re, uuid, os
import speech_recognition as sr
from telebot import types
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

bot = telebot.TeleBot('5552508957:AAFh29KIkY_i9PCztvUzMxxuynwx8m0evcU')

wikipedia.set_lang("ru")
language = "ru_RU"
r = sr.Recognizer()

def clean_str(r):
	r = r.lower()
	r = [c for c in r if c in alphabet]
	return ''.join(r)

alphabet = '1234567890-йцукенгшщзхъфывапролджэячсмитьбюёqwertyuiopasdfghjklzxcvbnm?%.,()!:;'

def update():
	with open('dialogues.txt', encoding='utf-8') as f:
		content = f.read()
	
	blocks = content.split('\n')
	dataset = []
	
	for block in blocks:
		replicas = block.split('\\')[:2]
		if len(replicas) == 2:
			pair = [clean_str(replicas[0]), clean_str(replicas[1])]
			if pair[0] and pair[1]:
				dataset.append(pair)
	
	X_text = []
	y = []
	
	for question, answer in dataset[:10000]:
		X_text.append(question)
		y += [answer]
	
	global vectorizer
	vectorizer = CountVectorizer()
	X = vectorizer.fit_transform(X_text)
	
	global clf
	clf = LogisticRegression()
	clf.fit(X, y)

update()

def get_generative_replica(text):
	text_vector = vectorizer.transform([text]).toarray()[0]
	question = clf.predict([text_vector])[0]
	return question

def getwiki(s):
    try:
        ny = wikipedia.page(s)
        wikitext=ny.content[:1000]
        wikimas=wikitext.split('.')
        wikimas = wikimas[:-1]
        wikitext2 = ''
        for x in wikimas:
            if not('==' in x):
                if(len((x.strip()))>3):
                   wikitext2=wikitext2+x+'.'
            else:
                break
        wikitext2=re.sub('\([^()]*\)', '', wikitext2)
        wikitext2=re.sub('\([^()]*\)', '', wikitext2)
        wikitext2=re.sub('\{[^\{\}]*\}', '', wikitext2)
        return wikitext2
    except Exception as e:
        return 'В энциклопедии нет информации об этом'

@bot.message_handler(commands=['start'])
def start_message(message):
	bot.send_message(message.chat.id,"Здравствуйте, Сэр.")

question = ""

def wrong(message):
	a = f"{question}\{message.text.lower()} \n"
	with open('dialogues.txt', "a", encoding='utf-8') as f:
		f.write(a)
	bot.send_message(message.from_user.id, "Готово")
	update()

def recognise(filename):
	with sr.AudioFile(filename) as source:
		audio_text = r.listen(source)
		try:
			text = r.recognize_google(audio_text,language="ru_RU")
			return text
		except:
			return ""

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
	command = message.text.lower()
	if command =="не так":
		bot.send_message(message.from_user.id, "а как?")
		bot.register_next_step_handler(message, wrong)
	else:
		global question
		question = command
		reply = get_generative_replica(command)
		if reply=="вики  ":
			bot.send_message(message.from_user.id, getwiki(command))
		else:
			bot.send_message(message.from_user.id, reply)

@bot.message_handler(content_types=['voice'])
def get_voice_messge(message):
	try:
		msg = bot.send_voice('5552508957:AAFh29KIkY_i9PCztvUzMxxuynwx8m0evcU', open('record.ogg', 'rb'))
		file_info = bot.get_file(msg.voice.file_id)
		path_name = os.path.splitext(file_info.file_path)
		file_name = os.path.basename(path_name)
		with open(file_name+'.oga', 'wb') as f:
			f.write(msg.content)
		text = recognise(file_name+'.wav') 
		question = get_generative_replica(format(text))
		bot.reply_to(message, question)
	except Exception as e:
		bot.send_message(message.from_user.id,  "Повторите еще раз")
	finally:
		os.remove(file_name+'.wav')
		os.remove(file_name+'.oga')

bot.polling(none_stop=True)