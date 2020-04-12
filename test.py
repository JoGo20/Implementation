import numpy as np

def _generateLibMap(element, turn, action):

    #visited=np.full(361,-1)
    connected = []
    newarr=np.array(np.zeros(361), dtype=np.int)
    def findLiberty(i,typ,taken,vis, action):
        if i in vis:
            return 0
        else:
            vis.append(i)
            if element[i]==0:
                if i in taken:
                    return 0
                else:
                    taken.append(i)
                    if element[action] == typ:
                        return 1 
                    else:
                        return 0    
            elif element[i]!=typ: 
                return 0
            else:
                action = i
                connected.append(i)
                place = (i) % 19
                isLower = (i >= 342)
                isUpper = (i <= 18)
                if i == 0:
                    return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)
                elif i==18:
                    return findLiberty(i-1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)
                elif i==342:
                    return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                elif i==360:
                    return findLiberty(i-1,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                elif place == 0:
                    return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                elif place == 18:
                    return findLiberty(i-1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                elif isUpper:
                    return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i-1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)
                elif isLower:
                    return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i-1,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                else:
                    return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i-1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
    def calcliberty(action, connected):  
        taken=[]
        vis=[]
        typ = turn
        place = (action) % 19
        isLower = (action >= 342)
        isUpper = (action <= 18)
        if element[action] == typ:
            if action == 0:
                liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)
            elif action==18:
                liberty = findLiberty(action-1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)
            elif action==342:
                liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
            elif action==360:
                liberty = findLiberty(action-1,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
            elif place == 0:
                liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
            elif place == 18:
                liberty = findLiberty(action-1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
            elif isUpper:
                liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action-1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)
            elif isLower:
                liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action-1,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
            else:
                liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action-1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
            
            newarr[connected] = (liberty+1)
            newarr[action] =  (liberty+1)
        
        else:
            if action == 0:
                liberty = findLiberty(action+1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action+19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
            elif action==18:
                liberty = findLiberty(action-1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action+19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]

            elif action==342:
                liberty = findLiberty(action+1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]

            elif action==360:
                liberty = findLiberty(action-1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
            elif place == 0:
                liberty = findLiberty(action+1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action+19,typ,taken,vis,action)
                
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
            elif place == 18:
                liberty = findLiberty(action-1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action+19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
            elif isUpper:
                liberty = findLiberty(action+1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action+19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
            elif isLower:
                liberty = findLiberty(action+1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
            else:
                liberty = findLiberty(action+1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-1,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action+19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
                liberty = findLiberty(action-19,typ,taken,vis,action)
                newarr[connected] = (liberty+1)
                del connected[:]
                del vis[:]
                del taken[:]
            
        del connected[:]
        del vis[:]
        del taken[:]
        return newarr  
    out=calcliberty(action, connected)
    return out

def _checkAllowance(element, turn, action):
    currLib = _generateLibMap(element,turn, action)
    tempBoard =np.copy(element)
    tempBoard[action] = turn 
    nextLib = _generateLibMap(tempBoard,-turn, action)
    tempBoard[nextLib == 1] = 0
    nextLib = _generateLibMap(tempBoard,turn, action)
    nextLib[nextLib == 1] =0
    if any(i > 0 for i in (nextLib - currLib)):
        return True
    return False

inp = np.array([
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
])

print(_checkAllowance(inp, -1, 1))