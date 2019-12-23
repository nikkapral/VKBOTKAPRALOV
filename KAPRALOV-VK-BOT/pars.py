import requests
from bs4 import BeautifulSoup
import re
import sqlite3
conn=sqlite3.connect('karoinfo.db')
cursor=conn.cursor()

def delete_tables(cursor):
    try:
        cursor.execute('drop table brand')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('drop table cinema_halls')
    except sqlite3.OperationalError:
        pass    
    try:
        cursor.execute('drop table cinemas')
    except sqlite3.OperationalError:
        pass    
    try:
        cursor.execute('drop table sessions')
    except sqlite3.OperationalError:
        pass    

def create_brand(cursor):
    try:
        cursor.execute('''CREATE TABLE brand(
                        id integer PRIMARY KEY,
                        name text NOT NULL)''')
    except sqlite3.OperationalError:
        pass
        
def create_cinema_halls(cursor):
    try:
        cursor.execute("""CREATE TABLE cinema_halls(
                    id integer PRIMARY KEY,
                    brand_id integer Not NULL,
                    website_id integer NULL,
                    name text NOT NULL,
                    address text NOT NULL,
                    metro text NULL,
                    phone text NULL,
                    FOREIGN KEY (brand_id) REFERENCES brand(id)
                    )""")
    except sqlite3.OperationalError:
        pass

def create_cinemas(cursor):
    try:
        cursor.execute("""CREATE TABLE cinemas(
                    id integer PRIMARY KEY,
                    website_id integer NULL,
                    name text NOT NULL,
                    duration text NULL,
                    genres text NULL
                    )""")
    except sqlite3.OperationalError:
        pass
        
def create_sessions(cursor):
    try:
        cursor.execute("""CREATE TABLE sessions(
                    id integer PRIMARY KEY,
                    cinema_id integer Not NULL,
                    hall_id integer Not NULL,
                    date date NOT NULL,
                    time time NOT NULL,
                    FOREIGN KEY (cinema_id) REFERENCES cinemas(id),
                    FOREIGN KEY (hall_id) REFERENCES cinema_halls(id)
                    )""")
    except sqlite3.OperationalError:
        pass
        
def create_tables(cursor):
    create_brand(cursor)
    create_cinema_halls(cursor)
    create_cinemas(cursor)
    create_sessions(cursor)
    
def add_brands(cursor):
    try:
        cursor.execute("insert into brand values (1, 'КАРО')")
        conn.commit()
    except sqlite3.IntegrityError:
        pass

def remove_all(string):
    pattern = re.compile('[А-Яа-яёЁ0-9 ]+')
    return pattern.findall(string)[0].strip()

def find_all_theaters_KARO(theatres):
    dicti = {}
    metro_class = 'cinemalist__cinema-item__metro__station-list__station-item'
    for theater in theatres:
        dicti[theater.findAll('h4')[0].text.strip()] = {
            'metro': [remove_all(i.text) for i in theater.findAll('li', class_=metro_class)], 
            'address': theater.findAll('p')[0].text.split('+')[0].strip(),
            'phone': '+' + theater.findAll('p')[0].text.split('+')[-1].strip(),
            'data-id': theater['data-id']}
    return dicti

def cinema_id_get(name,cinemas):
    for el in cinemas:
        if name==el[2]:
            return el[0]
    for el in cinemas:
        if (name in el[2]) or (el[2] in name):
            return el[0]

def main_parse_karo(cursor):
    url = "https://karofilm.ru"
    url_theaters = url + "/theatres"        
    r = requests.get(url_theaters)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        theatres = soup.findAll('li', class_='cinemalist__cinema-item')
        karo_theatres = find_all_theaters_KARO(theatres)
    else:
        pass
    id_=1
    for key,item in karo_theatres.items():
        try:
            metro=', '.join(item['metro'])
            if metro:
                metro="'"+metro+"'"
            else:
                metro='NULL'
            elements=[id_,1,item['data-id'],key,item['address'],metro,item['phone']]
            cursor.execute("insert into cinema_halls values ({},{},{},'{}','{}',{},'{}')".format(*elements))
            id_+=1
        except sqlite3.IntegrityError:
            pass
            break       
    films_all_class='afisha-item'
    r = requests.get(url)
    if r.status_code==200:
        films_all_parser=BeautifulSoup(r.text,'html.parser')
        all_films_list=films_all_parser.findAll('div',class_=films_all_class)
    else:
        pass        
    id_=1
    for element in all_films_list:
        data_id=element['data-id']
        name=element.findAll('h3')[0].text.strip()
        duration=element.findAll('span')[0].text
        try:
            genres='"'+element.findAll('p',class_='afisha-genre')[0].text+'"'
        except IndexError:
            genres='NULL'
        try:
            name=name.replace('\"','\'')
            cursor.execute(f'insert into cinemas values ({id_},{data_id}, "{name}", "{duration}", {genres})')
            id_+=1
        except sqlite3.IntegrityError:
            pass
            break     
    films_class='cinema-page-item__schedule__row'
    table_class='cinema-page-item__schedule__row__board-row'
    left_class=table_class+'__left'
    rignt_class=table_class+'__right'
    date_class='widget-select'
    id_=1
    for theater in karo_theatres:
        dates={}
        url_theater_id=url_theaters+'?id='+karo_theatres[theater]['data-id']
        r = requests.get(url_theater_id)
        if r.status_code==200:
            date_parser=BeautifulSoup(r.text,'html.parser')
            date_list=date_parser.findAll('select',class_=date_class)[0]
            date_list=[i['data-id'] for i in date_list.findAll('option')]
            for date in date_list: 
                url_theater_id_date=url_theater_id+'&date='+date
                r = requests.get(url_theater_id_date)
                session={}
                if r.status_code==200:
                    films_parser=BeautifulSoup(r.text,'html.parser')
                    films_list=films_parser.findAll('div',class_=films_class)
                    for film in films_list:
                        name=film.findAll('h3')
                        if name:
                            name=name[0].text.split(', ')
                            session_time={}
                            session_time['age']=name[1]
                            for i in film.findAll('div',class_=table_class):
                                time_D=i.findAll('div',class_=left_class)[0].text.strip()
                                time=i.findAll('div',class_=rignt_class)[0].findAll('a')
                                time=[j.text for j in time]
                                session_time[time_D]=time
                                for time_element in time:
                                    cinema_id=cinema_id_get(name[0].replace('\"','\''),cursor.execute(f'select * from cinemas').fetchall())
                                    hall_id=cursor.execute(f'select id from cinema_halls where name=\'{theater}\'').fetchall()[0][0]
                                    values=[id_,cinema_id,hall_id,date,time_element,'NULL']
                                    cursor.execute("insert into sessions values ({},{},{},'{}','{}')".format(*values))
                                    id_+=1
                            session[name[0]]=session_time
                else:
                    pass
                dates[date]=session
        else:
            pass
        karo_theatres[theater]['dates']=dates       


def main_parse(cursor,conn):
    delete_tables(cursor)
    create_tables(cursor)
    add_brands(cursor)
    main_parse_karo(cursor)
    conn.commit()

for i in range(10):
    try:
        main_parse(cursor,conn)
        break
    except:
        pass



