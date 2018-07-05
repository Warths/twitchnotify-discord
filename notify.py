from disco.bot import Plugin
from disco.types.user import GameType, Game, Status
from disco.types.message import MessageEmbed
import requests
import threading
import time
import datetime


class NotifyPlugin(Plugin):
    """ Class NotifyPlugin
    Class principale du module
    """

    @Plugin.listen('Ready')
    def ready(self):
        streams = [{'channel': 'Warths', 'color': 0xB6001C},
                   {'channel': 'ValentinStream', 'color': 0xDCC237},
                   {'channel': 'Kyriog', 'color': 0x26B5F0},
                   {'channel': 'Ragnar_oock', 'color': 0xA0A0A0},
                   {'channel': 'HeavyProjectbot', 'color': 0xB6001C},
                   {'channel': 'Air_One29', 'color': 0xBFBFBF}]
        streams = self.streams_init(streams)
        thread = threading.Thread(target=self.run, args=[streams])
        thread.daemon = True
        thread.start()

        presence_thread = threading.Thread(target=self.presence_run, args=[streams])
        presence_thread.daemon = True
        presence_thread.start()

    def run(self, streams):
        while True:
            for stream in streams:
                stream_request = self.is_online(stream['channel'])
                if stream_request:
                    stream['started_at'] = stream_request['data'][0]['started_at']
                    stream['title'] = stream_request['data'][0]['title']
                    stream['game_id'] = stream_request['data'][0]['game_id']
                    stream['user_id'] = stream_request['data'][0]['user_id']
                    if stream['momentum'] == 0:
                        stream = self.get_more_info(stream)
                        self.notification(stream)
                    if stream['momentum'] < 30:
                        stream['momentum'] += 5
                elif stream['momentum'] > 0:
                    stream['momentum'] -= 1
                elif stream['momentum'] == 0:
                    stream['started_at'] = None
            time.sleep(60)

    @staticmethod
    def is_online(user_login):
        request = requests.get('https://api.twitch.tv/helix/streams?user_login=%s' % user_login,
                               headers={'Client-ID': 'YOURCLIENTIDHERE',
                                        'Authorization': 'Bearer YOURTOKENHERE'})
        if request.status_code == 200 and str(request.json()['data']) != '[]':
            return request.json()
        else:
            return None

    @staticmethod
    def streams_init(streams):
        for stream in streams:
            stream['started_at'] = None
            stream['momentum'] = 0
        return streams

    @staticmethod
    def get_more_info(stream):
        request = requests.get('https://api.twitch.tv/helix/games?id=%s' % stream['game_id'],
                               headers={'Client-ID': 'qab2o1rz2l780rdbn7myuk5iyg4wra'})
        if request.status_code == 200 and str(request.json()['data']) != '[]':
            stream['game'] = request.json()['data'][0]['name'].capitalize()
        else:
            stream['game'] = 'Erreur'
        request = requests.get('https://api.twitch.tv/helix/users?login=%s' % stream['channel'],
                               headers={'Client-ID': 'qab2o1rz2l780rdbn7myuk5iyg4wra'})
        if request.status_code == 200 and str(request.json()['data']) != '[]':
            stream['logo'] = request.json()['data'][0]['profile_image_url']
            stream['display_name'] = request.json()['data'][0]['display_name']
        else:
            stream['logo'] = 'Erreur'
            stream['display_name'] = 'Erreur'
        return stream

    def notification(self, stream):
        print('Diffusion de l\'alerte de  %s dans #info-stream' % stream['channel'])
        embed = MessageEmbed(title=('%s est en Live sur Twitch !' % stream['display_name']),
                             url=('https://www.twitch.tv/%s' % stream['channel'].lower()),
                             color=stream['color'])
        embed.set_author(name=('%s - %s' % (stream['channel'], stream['game'])),
                         icon_url='https://static-cdn.jtvnw.net/badges/v1/3e636937-64e0-4e93-80c2-ec3c4389472e/1')
        embed.set_thumbnail(url=stream['logo'])
        embed.add_field(name='Jeux', value=stream['game'], inline=False)
        embed.add_field(name='Titre du Stream', value=stream['title'], inline=False)
        self.client.api.channels_messages_create(331202792213577731, embed=embed)

    def presence_run(self, streams):
        idle_content = '!next dans #bot'
        current_stream = None
        while True:
            online_stream = []
            for stream in streams:
                if stream['started_at'] is not None:
                    online_stream.append(stream)
            if online_stream.__len__() > 0:
                online_stream = sorted(online_stream,
                                       key=lambda x: datetime.datetime.strptime(x['started_at'], '%Y-%m-%dT%H:%M:%SZ'))
                stream = online_stream[0]
                if stream['channel'] != current_stream:
                    self.client.update_presence(Status.online,
                                                Game(type=GameType.streaming, name=stream['display_name'],
                                                     url='https://www.twitch.tv/%s' % stream['channel']))
                    print('%s en ligne. Changement du statut' % stream['display_name'])
                    current_stream = stream['channel']
            else:
                if current_stream != idle_content:
                    self.client.update_presence(Status.online, Game(type=GameType.listening, name=idle_content))
                    print('Aucun stream en ligne, diffusion du status par défaut')
                    current_stream = idle_content
            time.sleep(5)
