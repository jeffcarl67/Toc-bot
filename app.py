#coding:utf-8
from bottle import route, run, request
import json
import os
import requests
from transitions.extensions import GraphMachine
from bs4 import BeautifulSoup
import re
import random

GRAPH_URL = "https://graph.facebook.com/v2.6"
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PORT = os.environ.get("PORT")

url = 'https://www.cartoonmad.com/'
comic_id = ''
comic_num = ''
episode = ''
img_num = ''
episode_info = []
episode_dict = {}
img_base_url = ''

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(
            model=self,
            **machine_configs
        )
    def on_enter_init(self):
        global comic_id
        global comic_num
        global episode
        global img_num
        global episode_info
        global episode_dict
        global img_base_url
        print("I'm entering init")
        comic_id = ''
        comic_num = ''
        episode = ''
        img_num = ''
        episode_info = []
        episode_dict = {}
        img_base_url = ''
        print('CURRENT STATE: ' + machine.state)

    def on_exit_init(self):
        print('Leaving init')

    def on_enter_comic(self):
        global comic_id
        global comic_num
        global episode
        global img_num
        global episode_info
        global episode_dict
        global img_base_url
        print("I'm entering comic")
        comic_id = ''
        comic_num = ''
        episode = ''
        img_num = ''
        episode_info = []
        episode_dict = {}
        img_base_url = ''
        print('CURRENT STATE: ' + machine.state)

    def on_exit_comic(self):
        print('Leaving comic')

    def on_enter_episode(self):
        print("I'm entering episode")
        print('CURRENT STATE: ' + machine.state)

    def on_exit_episode(self):
        print('Leaving episode')

    def on_enter_image(self):
        print("I'm entering image")
        print('CURRENT STATE: ' + machine.state)

    def on_exit_image(self):
        print('Leaving image')



def find_comics(keyword):
    params = {'keyword':keyword.encode('big5'),'searchtype':'all'}
    r = requests.post('https://www.cartoonmad.com/search.html', data=params)
    r.encoding = 'big5'
    soup = BeautifulSoup(r.text, 'html.parser')
    comics = soup.find_all('a','a1')
    return comics

def find_episodes(comic_url):
    global episode_info
    global episode_dict
    print("find_apisodes: " + comic_url)
    comic_page = requests.get(comic_url)
    comic_page.encoding = 'big5'
    comic_page_soup = BeautifulSoup(comic_page.text, 'html.parser')
    episodes = comic_page_soup.find_all('a', target='_blank', href=re.compile('comic'))
    episode_names = [episode.string for episode in episodes]
    fonts = comic_page_soup.find_all('font', style="font-size:8pt;color: #888888;")
    episode_pages = [font.string for font in fonts]
    episode_info = zip(episode_names,episode_pages)
    #for i in episode_info:
    #    print(i[0] + i[1])
        #print(re.findall(r'd+',i[0]) + re.findall(r'd+',i[1]))
        #episode_dict[re.findall(r'd+',i[0])[0]] = int(re.findall(r'd+',i[1])[0])
    return episodes

def find_images(episode_url):
    print('find_images' + episode_url)
    img_page = requests.get(episode_url)
    img_page.encoding = 'big5'
    img_soup = BeautifulSoup(img_page.text, 'html.parser')
    imgs = img_soup.find_all('img',border="0",oncontextmenu="return false")
    return imgs

def get_comic_img_info(comic_url):
    global url
    img_url = []
    print(comic_url)
    episodes = find_episodes(comic_url)
    if episodes:
        images = find_images('https://www.cartoonmad.com'+episodes[0]['href'])
        if images:
            img_url = images[0]['src']
    #if img_url[0] == '/':
    #    return img_url.split('/')
    return img_url
        
    


machine = TocMachine(
    states=[
        'comic',
        'episode',
        'image',
        'init',
        'random',
        'recommend'
    ],
    transitions=[
        {
            'trigger': 'goto_episode',
            'source': 'comic',
            'dest': 'episode'
        },
        {
            'trigger': 'goto_image',
            'source': 'episode',
            'dest': 'image',
        },
        {
            'trigger': 'end',
            'source': [
                'episode',
                'image',
                'random',
                'recommend'
            ],
            'dest': 'init'
        },
        {
            'trigger': 'choose_comic',
            'source': 'init',
            'dest': 'comic'
        },
        {
            'trigger': 'choose_random',
            'source': 'init',
            'dest': 'random'
        },
        {
            'trigger': 'choose_recommend',
            'source': 'init',
            'dest': 'recommend'
        }
    ],
    initial='init',
    auto_transitions=False,
    show_conditions=True,
)
#machine.get_graph().draw('my_state_diagram.png', prog='dot')
#print(ACCESS_TOKEN)
#print(VERIFY_TOKEN)

@route("/webhook", method="GET")
def setup_webhook():
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return challenge

@route("/webhook", method="POST")
def webhook_handler():
    global url
    global comic_id
    global comic_num
    global episode
    global img_num
    global episode_info
    global episode_dict
    global img_base_url
    

    body = request.json
    #print('REQUEST BODY: ')
    #print(json.dumps(body, indent=2))

    if body['object'] == 'page':
        id = body['entry'][0]['messaging'][0]['sender']['id']
        text = body['entry'][0]['messaging'][0]['message']['text']
        sub_text = text if len(text) < 8 else text[0:8]
        #send_text_message(id,text)
        #send_img_url(id,'https://www.cartoonmad.com/cartoonimg/e267dk57cd6/8046/001/002.jpg')
        if machine.state == 'init':
            if text == 'random':
                machine.choose_random()
            elif text == 'recommend':
                machine.choose_recommend()
            elif text == 'comic':
                machine.choose_comic()
            else:
                send_text_message(id, 'please enter random or recommand or comic')
        elif machine.state == 'random':
            if text == 'start':
                random_c = chr(random.randint(97,122))
                comics = find_comics(random_c)
                comic_name = comics[random.randint(0, len(comics)-1)].string
                send_text_message(id, 'random comic is ' + comic_name)
            elif text == 'end':
                machine.end()
            else:
                send_text_message(id, 'please enter start or end')

        elif machine.state == 'recommend':
            if text == 'start':
                recommand_page = requests.get('https://www.cartoonmad.com/')
                recommand_page.encoding = 'big5'
                recommand_soup = BeautifulSoup(recommand_page.text, 'html.parser')
                recommands = recommand_soup.find_all('a', 'a1')
                msg = '\n'.join(i.string for i in recommands)
                msg_len = len(msg)
                base = 0
                while msg_len > 1000:
                    send_text_message(id, msg[base:base+1000])
                    base = base + 1000
                    msg_len = msg_len - 1000
                send_text_message(id, msg[base:base+1000])
            elif text == 'end':
                machine.end()
            else:
                send_text_message(id, 'please enter start or end')

        elif machine.state == 'comic':
            comics = find_comics(text)
            if len(comics) == 1:
                if comics[0].string == sub_text:
                    send_text_message(id, 'find '+text)
                    img_url = get_comic_img_info(url + comics[0]['href'])

                    if img_url[0] == '/':
                        img_base_url = url
                        info = img_url.split('/')
                        comic_id = info[2]
                        comic_num = info[3]
                        episode = info[4]
                        img_num = info[5]
                    else:
                        #send_text_message(id, 'sorry, cannot get img, please look for another comic')
                        #return
                        img_base_url = 'http://web3.cartoonmad.com'
                        info = img_url.split('/')
                        comic_id = info[3]
                        comic_num = info[4]
                        episode = info[5]
                        img_num = info[6]
                        
                    """
                    print('\n'.join(info))
                    #if info:
                    #    if len(info) == 5:
                    comic_id = info[2]
                    comic_num = info[3]
                    episode = info[4]
                    img_num = info[5]
                    """
                    machine.goto_episode()
                    epi = find_episodes(url + comics[0]['href'])
                    #print(len(episode_names))
                    #print(len(episode_pages))
                    msg = '\n'.join([i[0]+i[1] for i in episode_info])
                    msg_len = len(msg)
                    base = 0
                    while msg_len > 1000:
                        send_text_message(id, msg[base:base+1000])
                        base = base + 1000
                        msg_len = msg_len - 1000
                    send_text_message(id, msg[base:base+1000])

                    #send_text_message(id, '\n'.join([i[0]+i[1] for i in episode_info]))
                    #print(episode_dict)
                     
                else:
                    send_text_message(id, 'is this what you want? please enter full name' + comics[0].string)
            elif len(comics) == 0:
                send_text_message(id, 'can not find any comic')
            else:
                
                for comic in comics:
                    if comic.string == sub_text:
                        send_text_message(id, 'find '+text)
                        img_url = get_comic_img_info(url + comics[0]['href'])

                        if img_url[0] == '/':
                            img_base_url = url
                            info = img_url.split('/')
                            comic_id = info[2]
                            comic_num = info[3]
                            episode = info[4]
                            img_num = info[5]
                        else:
                            #send_text_message(id, 'sorry, cannot get img, please look for another comic')
                            #return
                            img_base_url = 'http://web3.cartoonmad.com'
                            info = img_url.split('/')
                            comic_id = info[3]
                            comic_num = info[4]
                            episode = info[5]
                            img_num = info[6]
                        machine.goto_episode()
                        epi = find_episodes(url + comic['href'])
                        #print(len(episode_names))
                        #print(len(episode_pages))
                        msg = '\n'.join([i[0]+i[1] for i in episode_info])
                        msg_len = len(msg)
                        base = 0
                        while msg_len > 1000:
                                send_text_message(id, msg[base:base+1000])
                                base = base + 1000
                                msg_len = msg_len - 1000
                        send_text_message(id, msg[base:base+1000]) 
                        #send_text_message(id, '\n'.join([i[0]+i[1] for i in episode_info]))
                        #print(episode_dict)
                        return
                
                send_text_message(id, '\n'.join([comic.string for comic in comics]))
        elif machine.state == 'episode':
            if text.isdigit():
                if len(text) <= 3:
                    episode = "{:0>3d}".format(int(text))
                    print('img_num:' + img_num)
                    print(url+'cartoonimg/'+comic_id+'/'+comic_num+'/'+episode+'/'+img_num)

                    if img_base_url == url:
                        ret = send_img_url(id,url+'cartoonimg/'+comic_id+'/'+comic_num+'/'+episode+'/'+img_num)
                    else:
                        ret = send_img_url(id,img_base_url+'/'+comic_id+'/'+comic_num+'/'+episode+'/'+img_num)
                    if ret != 200:
                        machine.end()
                        send_text_message(id, 'sorry, cant get image, please choose another comic')
                    else:
                        machine.goto_image()
            elif text == 'end':
                machine.end()
                #send_text_message(id, 'comic?')
            else:
                send_text_message(id, 'please enter episode number or end')

        elif machine.state == 'image':
            if text == 'next':
                num = int(img_num.split('.')[0])
                num = num + 1
                img_num = "{:0>3d}".format(int(num)) + '.jpg'
                #send_img_url(id,url+'cartoonimg/'+comic_id+'/'+comic_num+'/'+episode+'/'+img_num)
                if img_base_url == url:
                    ret = send_img_url(id,url+'cartoonimg/'+comic_id+'/'+comic_num+'/'+episode+'/'+img_num)
                else:
                    ret = send_img_url(id,img_base_url+'/'+comic_id+'/'+comic_num+'/'+episode+'/'+img_num)
                if ret != 200:
                    machine.end()
                    send_text_message(id, 'this episode end, please choose another comic')
            elif text == 'end':
                machine.end()
                send_text_message(id, 'comic?')
            else:
                send_text_message(id, 'please enter next or end')
        else:
            pass            




def send_text_message(id, text):
    url = "{0}/me/messages?access_token={1}".format(GRAPH_URL, ACCESS_TOKEN)
    payload = {
        "recipient": {"id": id},
        "message": {"text": text}
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print("Unable to send message: " + response.text)
    return response.status_code

def send_img_url(id, img_url):
    url = "{0}/me/messages?access_token={1}".format(GRAPH_URL, ACCESS_TOKEN)
    payload = {
        "recipient": {"id": id},
        "message": {
            "attachment": {
                "type":"image",
                "payload":{
                    "url":img_url
                }
            }
        }
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print("Unable to send message: " + response.text)
    return response.status_code

run(host="localhost", port=PORT, debug=True, reloader=True)