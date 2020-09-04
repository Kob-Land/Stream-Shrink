import os
import urllib.request
import json
from twitchio.ext import commands
import random
import time
import sys
# set up the bot
#
initial_chans=[os.environ['CHANNEL']]
bots = commands.Bot(
    irc_token=os.environ['TMI_TOKEN'],
    client_id=os.environ['CLIENT_ID'],
    nick=os.environ['BOT_NICK'],
    prefix=os.environ['BOT_PREFIX'],
    initial_channels=[os.environ['CHANNEL']]
)
def isIn(element, list):
    for x in list:
        if element==x:
            return True
    return False
async def chatters(chanName):
    chusList=[]
    channel = chanName.lower()
    f=urllib.request.urlopen("https://tmi.twitch.tv/group/user/%s/chatters"% channel)
    data=json.loads(f.read().decode("utf-8"))
    os.system('cls')
    print('Total chatters in %s: %d'%(channel,data['chatter_count']))
    print(data)
    if data['chatters']:
        if data['chatters']['viewers']:
            for user in data['chatters']['viewers']:
                chusList.append(user)
    return chusList
class channelInf:
    channelName=''
    viplist=[]
    blacklist=[]
    keeplist=[]
    userList=[]
    userCount=9999999999
    maxInChat=9999999999
    waitTime=1200
    timePassed= waitTime-5
    timeLastSwapped=time.time()
    def name(self, name):
        self.channelName=name
    def Viplist(self, user):
        if isIn(user, self.blacklist):
            self.blacklist.remove(user)
        self.viplist.append(user)
    def Blacklist(self, user):
        if isIn(user, self.viplist):
            self.viplist.remove(user)
        self.blacklist.append(user)
    def unBlacklist(self, user):
        if isIn(user, self.blacklist):
            self.blacklist.remove(user)
    def unViplist(self, user):
        if isIn(user, self.viplist):
            self.viplist.remove(user)
    def Keeplist(self, user):
        if not isIn(user, self.viplist):
            self.keeplist.append(user)
        if isIn(user, self.blacklist):
            self.blacklist.remove(user)
    def unKeeplist(self, user):
        self.keeplist.remove(user)
    def setUserCount(self, amount):
        self.userCount=amount
    def setMaxInChat(self, amount):
        self.maxInChat=amount
    def setWaitTime(self, sec):
        self.waitTime=sec
    def resetTimePassed(self):
        self.timePassed=0
    def markSwapTime(self):
        self.timeLastSwapped=time.time()
    async def update(self):
        ch=self.channelName
        userCount=len(await chatters(ch))
        self.userList=[]
        for x in await chatters(ch):
            self.userList.append(x)
        self.timePassed=time.time()-self.timeLastSwapped
        if self.maxInChat>len(self.userList):
            self.setMaxInChat(len(self.userList))
        if self.timePassed>=self.waitTime:
            await self.swap()
    async def swap(self):
        chann=bots.get_channel(self.channelName)
        us2=[]
        print("trying to enter loop 1")
        while len(self.keeplist) < self.maxInChat:
            print("going through another user")
            candidate=random.choice(self.userList)
            if not isIn(candidate,self.blacklist) and not isIn(candidate, us2):
                self.Keeplist(candidate)
                us2.append(candidate)
        for user in self.userList:
            if (not isIn(user,self.viplist)) and (not isIn(user,self.keeplist)):
                await chann.timeout(user, int(self.waitTime), (user+" was lost in the swap"))
            if isIn(user, self.keeplist) or isIn(user, self.viplist):
                await chann.timeout(user, 1, (user+" has returned"))
        self.keeplist.clear()
        self.markSwapTime()
async def updateAllChannelInf(listChannelInf):
    for chan in listChannelInf:
        await chan.update()

channelInfList=[]


@bots.event
async def event_ready():
    'Called once when the bot goes online.'
    print(f"{os.environ['BOT_NICK']} is online!")
    ws = bots._ws  # this is only needed to send messages within event_ready
    chan = os.environ['CHANNEL']
    await ws.send_privmsg(chan, f"/me has landed!")
    newChanInf=channelInf()
    newChanInf.name(chan[1:])
    channelInfList.append(newChanInf)

@bots.event
async def event_message(ctx):
    print(f"message received")
    print(ctx.content)
    await updateAllChannelInf(channelInfList)
    'Runs every time a message is sent in chat.'
    if ctx.author.name.lower() == os.environ['BOT_NICK'].lower():
        return
    pos=get_channelInf_pos(ctx)
    if channelInfList[pos].maxInChat>len(channelInfList[pos].userList):
        channelInfList[pos].setMaxInChat(len(channelInfList[pos].userList))
    await bots.handle_commands(ctx)

@bots.command(name='test')
async def test(ctx):
    await ctx.channel.send('test passed!')
#####################
@bots.command(name='untimeout')
async def untimeout(ctx):
    message=ctx.content[11:]
    if ctx.author.is_mod:
        try:
            await ctx.channel.timeout(message, 1, (message+" has returned"))
        except:
            await ctx.channel.send(f'something went wrong')

def get_channelInf_pos(ctx):
    count=0
    pos=0
    for ci in channelInfList:
        if ci.channelName[1:]==ctx.channel.name:
            pos=count
        count=count+1
    return pos

@bots.command(name='max')
async def max(ctx):
    pos=get_channelInf_pos(ctx)
    message=ctx.content[5:]
    if ctx.author.is_mod:
        try:
            max=int(message)
            if max>len(channelInfList[pos].userList):
                max=len(channelInfList[pos].userList)
            channelInfList[pos].setMaxInChat(max)
            await ctx.channel.send('max set to %i' % max)
        except:
            await ctx.channel.send('invalid number')

@bots.command(name='joinch')
async def joinch(ctx):
    pos=get_channelInf_pos(ctx)
    message=ctx.content[9:]
    if ctx.author.name.lower()==message.lower() and ctx.channel.name.lower()=='streamshrink':
        c=str('#'+message)
        if not isIn(c,initial_chans):
            newChanInf=channelInf()
            newChanInf.name(message)
            channelInfList.append(newChanInf)
            await ctx.channel.send("the bot is now in %s's channel. please mod it in order for it to fully function" % message)
            await bots.join_channels([message])
            await bots.getchannel(message).send("Hi! please mod me in order for me to fully function")
    else:
        await ctx.channel.send('you cannot sent me to the "%s" channel because that is not your channel or it is already there'% message.lower())

@bots.command(name='manswap')
async def manswap(ctx):
    pos=get_channelInf_pos(ctx)
    if ctx.author.is_mod:
        await channelInfList[pos].swap()

@bots.command(name='help')
async def manswap(ctx):
    if ctx.author.is_mod:
        await ctx.channel.send('use --help to get the function list')
        await ctx.channel.send('use "--joinch <your channel>" to make the bot join your channel.')
        await ctx.channel.send('use "--test" to make sure the bot is working in your stream')
        await ctx.channel.send('use "--viplist <user>" to make sure a viewer isnt removed in the swaps. this puts them on a VIP list')
        await ctx.channel.send('use "--blacklist <user>" to make sure a viewer is removed in the swaps and cannot return. this puts them on a blacklist')
        await ctx.channel.send('use "--unviplist <user>" to take a user off of your VIP list.')
        await ctx.channel.send('use "--unblacklist <user>" to take a user off of your blacklist.')
        await ctx.channel.send('use "--stime <minutes>" to change how many minutes it takes for the swap to happen. The default is 6 minutes')
        await ctx.channel.send('use "--max <users>" to change how many users will remain in the chat after a swap. The default is the entire chat')
        await ctx.channel.send('use "--untimeout <user>" to bring back someone who was timed out by the bot')
        await ctx.channel.send('use "--manswap" to make the swap happen manually.')
@bots.command(name='stime')
async def stime(ctx):
    pos=get_channelInf_pos(ctx)
    message=ctx.content[7:]
    if ctx.author.is_mod:
        try:
            stime=round(float(message),2)
            channelInfList[pos].setWaitTime(stime*60)
            await ctx.channel.send('wait time set to %.2f minutes' % stime)
        except:
            await ctx.channel.send('invalid number')

@bots.command(name='viplist')
async def cViplist(ctx):
    pos=get_channelInf_pos(ctx)
    message=ctx.content[10:]
    if ctx.author.is_mod:
        channelInfList[pos].Viplist(message)
        await ctx.channel.send('%s has been added to the VIP list' % message)

@bots.command(name='unviplist')
async def cUnViplist(ctx):
    pos=get_channelInf_pos(ctx)
    message=ctx.content[12:]
    if ctx.author.is_mod:
        try:
            channelInfList[pos].unViplist(message)
            await ctx.channel.send('%s has been removed from the VIP list' % message)
        except:
            await ctx.channel.send('not a user')

@bots.command(name='blacklist')
async def cBlacklist(ctx):
    pos=get_channelInf_pos(ctx)
    message=ctx.content[12:]
    if ctx.author.is_mod:
        try:
            channelInfList[pos].Blacklist(message)
            await ctx.channel.send('%s has been blacklisted' % message)
        except:
            await ctx.channel.send('not a user')

@bots.command(name='unblacklist')
async def cUnBlacklist(ctx):
    pos=get_channelInf_pos(ctx)
    message=ctx.content[14:]
    if ctx.author.is_mod:
        try:
            channelInfList[pos].unBlacklist(message)
            await ctx.channel.send('%s has been removed from the blacklist' % message)
        except:
            await ctx.channel.send('not a user')


bots.run()
