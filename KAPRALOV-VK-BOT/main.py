import sqlite3
import random
import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
conn=sqlite3.connect('karoinfo.db')
cursor=conn.cursor()

def write_msg(user_id, message,keyboard=None):
    random_id=random.getrandbits(31) * random.choice([-1, 1])
    vk.method('messages.send', {'user_id': user_id, 'message': message,'random_id':random_id,'keyboard':keyboard})

def cinema_halls(brand):
    brand_id=cursor.execute(f"SELECT id FROM brand WHERE name='{brand}'").fetchall()[0][0]
    return [elem[0] for elem in cursor.execute(f"SELECT name FROM cinema_halls WHERE brand_id='{brand_id}'").fetchall()]

def dates(cinema_hall):
    cinema_hall_id=cursor.execute(f"SELECT id FROM cinema_halls WHERE name='{cinema_hall}'").fetchall()[0][0]
    date_list=[elem[0] for elem in cursor.execute(f"SELECT date FROM sessions WHERE hall_id='{cinema_hall_id}'").fetchall()]
    date_list=list(set(date_list))
    date_list.sort()
    return date_list

def cinemas(date,cinema_hall):
    cinema_hall_id=cursor.execute(f"SELECT id FROM cinema_halls WHERE name='{cinema_hall}'").fetchall()[0][0]
    cinema_list=cursor.execute(f"SELECT cinema_id FROM sessions WHERE (hall_id='{cinema_hall_id}'and date='{date}') ").fetchall()
    for i,cinema in enumerate(cinema_list):
        cinema_list[i]=cursor.execute(f"SELECT name FROM cinemas WHERE id='{cinema[0]}'").fetchall()[0][0]
    cinema_list=list(set(cinema_list))
    cinema_list.sort()
    return cinema_list
def create_keyboard(list_buttons=[],brand=None,cinema_hall=None,date=None,cinema=None,next_=0):   
    keyboard={"one_time": True}
    list_buttons=list_buttons[32*next_:]
    if next_:
        payload={'b':brand,'h':cinema_hall,'d':date,'c':cinema,'n':next_-1}
        button_previous={"action": {"type": "text","payload": payload,"label": 'Назад'},
                        "color": "negative"}
    else:
        button_previous=None
    if len(list_buttons)>32:
        payload={'b':brand,'h':cinema_hall,'d':date,'c':cinema,'n':next_+1}
        button_next={"action": {"type": "text","payload": payload,"label": 'Далее'},
                     "color": "positive"}
    else:
        button_next=None
    list_buttons=list_buttons[:32]
    buttons=[]
    for i,button in enumerate(list_buttons):
        payload={'b':brand,'h':cinema_hall,'d':date,'c':cinema,'n':0}
        if not payload['b']:
            payload['b']=button
        elif not payload['h']:
            payload['h']=button
        elif not payload['d']:
            payload['d']=button
        else:
            payload['c']=button
        button={"action": {"type": "text","payload": payload,"label": next_*32+i+1},
                "color": "secondary"}
        buttons.append(button)
    list_buttons=[]
    while buttons:  
        list_buttons.append(buttons[:4])
        buttons=buttons[4:]
    if button_next and button_previous:
        list_buttons.append([button_previous,button_next])
    elif button_next:
        list_buttons.append([button_next])
    elif button_previous:
        list_buttons.append([button_previous])
    else:
        pass
    button={"action": {"type": "text","payload": None,"label": 'В меню'},
                "color": "primary"}
    
    list_buttons.append([button])
    keyboard["buttons"]=list_buttons 
    keyboard=str(json.dumps(keyboard))
    return keyboard

def information(brand,cinema_hall,date,cinema):
    info=cursor.execute(f"SELECT address,phone,id FROM cinema_halls where NAME='{cinema_hall}'").fetchall()[0]
    address=info[0]
    phone=info[1]
    hall_id=info[2]
    info=cursor.execute(f"SELECT duration,genres,id FROM cinemas WHERE name='{cinema}'").fetchall()[0]
    duration=info[0]
    genres=info[1]
    cinema_id=info[2]
    info=cursor.execute(f"select time from sessions where (cinema_id='{cinema_id}' and hall_id='{hall_id}' and date='{date}')").fetchall()
    hours = int(duration)//60
    minutes = int(duration) - hours*60
    text=f'''Сеть кинотеатров: {brand}
Информация о кинотеатре:
Кинозал: {cinema_hall}
Адрес: {address}
Телефон: {phone}

Информация о фильме:
Название кинофильма: {cinema}
Продолжительность: {hours} часов {minutes} минут
Жанр кинофильма: {genres}
Доступные сеансы:'''
    for item in info:
        text=text+f'\nсеанс в: {item[0]}'
    return text


brands=[elem[0] for elem in cursor.execute("SELECT name FROM brand").fetchall()]
token = "df03d8fe6624fdf9e94553cb876d65e63da4059a840ff148d0c14bdd8c47f65e55c7c17edcc5d4a993f38"
vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            request = event.text.lower()
            payload=json.loads(event.extra_values.get('payload','""'))
            if not(payload):
                write_msg(event.user_id, 'Выберите бренд\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(brands)]),create_keyboard(brands))
            elif payload['b']and not payload['h']:
                next_=payload['n']
                brand=payload['b']
                cinema_hall=cinema_halls(brand)
                write_msg(event.user_id,'Выберите кинотеатр\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(cinema_hall)]),create_keyboard(cinema_hall,brand,next_=next_))
            elif payload['b']and payload['h'] and not payload['d']:
                next_=payload['n']
                brand=payload['b']
                cinema_hall=payload['h']
                date=dates(cinema_hall)
                write_msg(event.user_id,'Выберите дату\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(date)]),create_keyboard(date,brand,cinema_hall,next_=next_))
            elif payload['b']and payload['h'] and payload['d'] and not payload['c']:
                next_=payload['n']
                brand=payload['b']
                cinema_hall=payload['h']
                date=payload['d']
                cinema=cinemas(date,cinema_hall)
                write_msg(event.user_id,'Выберите фильм\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(cinema)]),create_keyboard(cinema,brand,cinema_hall,date,next_=next_))
            else:
                brand=payload['b']
                cinema_hall=payload['h']
                date=payload['d']
                cinema=payload['c']
                text=information(brand,cinema_hall,date,cinema)
                write_msg(event.user_id,text,create_keyboard())