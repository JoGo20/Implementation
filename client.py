import asyncio
import json
import websockets
from enum import Enum
import random
import threading 
import sys


class States(Enum):
    INIT = 1
    READY = 2
    IDLE = 3
    THINK = 4
    
class GameServer:
    def __init__(self):
        self.State = States.INIT    
        self.GameConfig = None
        self.PlayerColor = None # "B" / "W"
        self.Socket = None
        self.Name = None
        self.oppmove=[0,0]
        self.LastOppMove = None  # move--> type,point --> ['row'], ['column']
        self.RemainTime  =  None
        self.score = None   # score["B"]
        self.validmove=True
        # Additonal Information
        self.Winner = None
        self.board = None  
        self.endgame=None
        self.pause = False
        self.winner = None
    def GetGameConfig(self):
        return self.GameConfig
    def getOppMove(self, i):
        return self.oppmove[i]
    def UpdateScoreAndTime(self,Msg):
        self.RemainTime = {
                                    "B": Msg['players']['B']['remainingTime'] ,
                                    "W": Msg['players']['W']['remainingTime']
                                } 
        self.score = {
                            "B": Msg['players']['B']['score'],
                            "W": Msg['players']['W']['score'] 
        }


async def ReadyState(GameInfo):
    print("I am Ready!")

    
    response = await GameInfo.Socket.recv()
    response = json.loads(response)
    if(response['type'] == 'START'):
        # State = States.READY
        GameInfo.endgame=False
        GameInfo.GameConfig = response['configuration']
        GameInfo.PlayerColor = response['color']
        GameInfo.board = GameInfo.GameConfig['initialState']['board']
        print(GameInfo.GameConfig['initialState']['turn'])
        print(GameInfo.PlayerColor)
        print(GameInfo.GameConfig['moveLog'])
        MoveLog = GameInfo.GameConfig['moveLog']
        # print(GameInfo.PlayerColor == GameInfo.GameConfig['initialState']['turn'])
        print( ( (GameInfo.PlayerColor == GameInfo.GameConfig['initialState']['turn'] and len(MoveLog) % 2 == 0) or (GameInfo.PlayerColor != GameInfo.GameConfig['initialState']['turn'] and len(MoveLog) % 2 != 0)))
        if ( (GameInfo.PlayerColor == GameInfo.GameConfig['initialState']['turn'] and len(MoveLog) % 2 == 0) or (GameInfo.PlayerColor != GameInfo.GameConfig['initialState']['turn'] and len(MoveLog) % 2 != 0)) :
            GameInfo.State = States.THINK
        else:
            GameInfo.State = States.IDLE
        # print(GameInfo.PlayerColor)
    elif response['type'] == 'END':
        GameInfo.pause = response['reason'] == 'pause'
        GameInfo.winner = response['winner']
        print("End")
        GameInfo.UpdateScoreAndTime(response)
        GameInfo.endgame=True
        #Write in file for the GUI
    else:
        print("Nothing")
            
    pass
async def IdleState(GameInfo):

    print("Idle")
    
    Msg = await GameInfo.Socket.recv() 
    Msg = json.loads(Msg)
    print(Msg)
    if Msg['type'] == "MOVE" :
        GameInfo.State = States.THINK
        GameInfo.LastOppMove = Msg['move']
        recmov(GameInfo)
        GameInfo.RemainTime = Msg['remainingTime']  
        
    elif Msg['type'] == 'END' :
        GameInfo.pause = Msg['reason'] == 'pause'
        GameInfo.winner = Msg['winner']
        GameInfo.State = States.READY
        GameInfo.endgame=True
        GameInfo.UpdateScoreAndTime(Msg)


def MakeMove(GameInfo, x,y,typ):

    print("row: ", x)
    print("column: ", y)
    if typ==1:
        PlaceMove = {'type' : 'pass'} 
    else:
        PlaceMove = {
                    'type' : 'place',
                    'point': { 
                                'row':x,
                                'column':y
                            }
    #ResignMove = {'type': 'resign'}
    
    #print(GameInfo.LastOppMove)
    
    # IMPORTANT
    # 
    # Recieved Move Message Format 
    # 
    # {'type' : 'pass'}
    # OR
    # {'type': 'resign'}
    # OR 
    # {
    #     'type' : 'place',
    #     'point': { 
    #                 'row':x,
    #                 'column':y
    #             }
        
    # }
    #
    # Also the sent message should be the same format
    
    
    
    #x = random.randrange(0,20)
    #y = random.randrange(0,20)

                 
                }

    return PlaceMove
    

async def ThinkState(GameInfo, x,y, typ):

    print("Thinking")
    # while 1:
    #     print('x')
    #     pass
    Msg = None
    # print(GameInfo.GameConfig['initialState']['board'])
    while True:    
        # x =  input('Enter move')
        MsgToSend = {
                        'type': 'MOVE',
                        'move': MakeMove(GameInfo, x,y, typ)
                    }
        
        print(MsgToSend)
        x = await GameInfo.Socket.send( json.dumps(MsgToSend) )
        
        Msg = await GameInfo.Socket.recv()
        Msg = json.loads(Msg)
        print(Msg)
        
        if Msg['type'] == 'END':
            GameInfo.pause = Msg['reason'] == 'pause'
            GameInfo.winner = Msg['winner']
            GameInfo.State = States.READY
            GameInfo.endgame=True
            GameInfo.UpdateScoreAndTime(Msg)
            return
        elif Msg['type'] == "VALID":
            GameInfo.State = States.IDLE
            GameInfo.validmove=True
            GameInfo.RemainTime = Msg['remainingTime']
            return
        elif Msg['type'] == "INVALID":
            GameInfo.State = States.THINK
            GameInfo.validmove=False            
            GameInfo.RemainTime = Msg['remainingTime']
            return
        
        GameInfo.RemainTime = Msg['remainingTime']
    
    pass


async def InitState(GameInfo, name):
    print("Connecting to Socket")
    try:
        GameInfo.Socket = await websockets.connect('ws://localhost:8080',ping_interval=100)
        print("let's start!")
        t2 = threading.Thread(target=ping_pong_handler, args=[GameInfo]) # ping pong
        t2.start()
        
        response = await GameInfo.Socket.recv()
        # asyncio.get_event_loop().run_until_complete(Pong())
        print(response)
        
        x = await GameInfo.Socket.send(json.dumps({'type': 'NAME', 'name': str(name)}))   
        GameInfo.State = States.READY
        return True
    except:
        print("Connection Failed")
        return False


    
async def ping_pong(GameInfo):
    print("Ping")
    while True:
        try:
            await GameInfo.Socket.pong()
            await asyncio.sleep(0.5)
        except Exception as e:
            print(e)
            return

def recmov(GameInfo):
    if GameInfo.LastOppMove['type']=="pass":
        GameInfo.oppmove=[-1,-1]
    elif GameInfo.LastOppMove['type']=="resign":
        GameInfo.oppmove=[-2,-2]
    else:
        GameInfo.oppmove=[GameInfo.LastOppMove['point']['row'],GameInfo.LastOppMove['point']['column']]

def ping_pong_handler(GameInfo):
    asyncio.new_event_loop().run_until_complete(ping_pong(GameInfo))


    