
import pygame
from sys import exit
import numpy as np
import math
import os
from pygame.locals import *
BOARD_SIZE = (820, 820)
SCREEN_SIZE = (1200,820)
WHITE = (220, 220, 220)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0) 
BLUE = (0, 0, 128)
RED=(128,128,128)
#BGC=(220,220,220)
BGC=(255,255,255)
whiteScorePos=[1105,100]
blackScorePos=[915,100]



class Stone():
    def __init__(self, point, color,screen,background):
        """Create, initialize and draw a stone."""
        self.point = point
        self.color=color
        self.background=background
        self.screen=screen
        self.coords = (5 + self.point[0] * 40, 5 + self.point[1] * 40)
        

    def draw(self):
        """Draw the stone as a circle."""
        pygame.draw.circle(self.screen, self.color, self.coords, 20, 0)

    def remove(self):
        """Remove the stone from board."""
        blit_coords = (self.coords[0] - 20, self.coords[1] - 20)
        area_rect = pygame.Rect(blit_coords, (40, 40))
        self.screen.blit(self.background, blit_coords, area_rect)
        


class Board():
    def __init__(self,screen,background):
        """Create, initialize and draw an empty board."""
        self.background=background
        self.outline = pygame.Rect(45, 45, 720, 720)
        self.screen=screen
        self.draw()

    def draw(self):
        """Draw the board to the background and blit it to the screen.

        The board is drawn by first drawing the outline, then the 19x19
        grid and finally by adding hoshi to the board. All these
        operations are done with pygame's draw functions.

        This method should only be called once, when initializing the
        board.

        """
        self.screen.fill(BGC)
        pygame.draw.rect(self.background, BLACK, self.outline, 3)
        
        # Outline is inflated here for future use as a collidebox for the mouse
        self.outline.inflate_ip(20, 20)
        for i in range(18):
            for j in range(18):
                rect = pygame.Rect(45 + (40 * i), 45 + (40 * j), 40, 40)
                pygame.draw.rect(self.background, BLACK, rect, 1)
        for i in range(3):
            for j in range(3):
                coords = (165 + (240 * i), 165 + (240 * j))
                pygame.draw.circle(self.background, BLACK, coords, 5, 0)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()
        
    def drawboard(self,fullboard):
        for i in range(361):
            y =  (math.floor(i / 19))+1
            x =  (i % 19)+1
            if fullboard[i]==1:
                added_stone = Stone((x, y), BLACK,self.screen,self.background)
                added_stone.draw()
            elif fullboard[i]==-1:
                added_stone = Stone((x, y), WHITE,self.screen,self.background)
                added_stone.draw()
            else:
                pass
        pygame.display.update()
    def clearboard(self):
        for i in range(361):
            y =  (math.floor(i / 19))+1
            x =  (i % 19)+1
            added_stone = Stone((x, y), BLACK,self.screen,self.background)
            added_stone.remove()
        
    def text_objects(self,text, font,color):
        textSurface = font.render(text, True, color)
        return textSurface, textSurface.get_rect()

    def message_display(self,text,point,color):
        largeText = pygame.font.Font('FFF_Tusj.ttf',30)
        TextSurf, TextRect = self.text_objects(text, largeText,color)
        TextRect.center = (point[0],point[1])
        self.screen.blit(TextSurf, TextRect)

    def updateScoreMsg(self,score):
        pygame.draw.rect(self.screen, BGC,(820,0,1200,500))
        self.message_display("SCORE",[1010,20],RED)
        self.message_display("BLACK",[915,60],BLACK)
        self.message_display("WHITE",[1105,60],WHITE)
        self.message_display(str(score[0]),[1105,100],WHITE)
        self.message_display(str(score[1]),[915,100],BLACK)
        pygame.display.update()


    def updateFullScoreMsg(self,score, prisoners):
        pygame.draw.rect(self.screen, BGC,(820,0,1200,500))
        self.message_display("SCORE",[1010,20],RED)
        self.message_display("BLACK",[915,60],BLACK)
        self.message_display("WHITE",[1105,60],WHITE)
        self.message_display(str(score[0]),[1105,100],WHITE)
        self.message_display(str(score[1]),[915,100],BLACK)
        self.message_display("PRISONERS",[1010,140],RED)
        self.message_display(str(prisoners[0]),[1105,180],WHITE)
        self.message_display(str(prisoners[1]),[915,180],BLACK)

        pygame.display.update()


    def updateMsg(self,turnmsg,statusmsg,color):
        pygame.draw.rect(self.screen, BGC,(820,500,1200,820))
        self.message_display(statusmsg,[1010,640],color)
        self.message_display(turnmsg,[1010,680],RED)
        pygame.display.update()
    
    def startmenu(self,startbg,aibg,brain):
         pygame.draw.rect(self.screen, BGC,(820,0,1200,820))
         self.screen.blit(startbg, (910, 500))
         self.screen.blit(aibg, (865, 50))
         self.screen.blit(brain, (1048, 50))
         pygame.display.update()

    def getUserAction(self,passbg,usercolor, home):
        self.screen.blit(passbg, (910, 300))
        self.screen.blit(home, (960, 700))
        pygame.display.update()
        while(True):
            #guiboard.updateMsg("","Its Your Turn",RED)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.outline.collidepoint(event.pos):
                            x = int(round(((event.pos[0] - 5) / 40.0), 0))
                            y = int(round(((event.pos[1] - 5) / 40.0), 0))
                            x=x-1
                            y=y-1
                            action=y*19+x
                            print("User action = ", action)
                            pygame.draw.rect(self.screen, BGC,(820,0,1200,500))
                            return action
                        else:
                            x = event.pos[0]
                            y = event.pos[1]
                            if x>910 and x<1096 and y>300 and y<478:
                                if usercolor=="BLACK":
                                    action=361
                                    pygame.draw.rect(self.screen, BGC,(820,0,1200,500))
                                    return action
                                else:
                                    action=362
                                    pygame.draw.rect(self.screen, BGC,(820,0,1200,500))
                                    return action
                            elif x>960 and x<1060 and y>700 and y<800:
                                return -1





