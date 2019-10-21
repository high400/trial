import math
import pygame
import os

boardfix = [
    ["┌","┬","┐"],
    ["├","┼","┤"],
    ["└","┴","┘"],
];

#Globale verdier
alphaValueOffset = 0x41;

#Hjelpe funksjoner
def index2pos(index):
    return (index%8,math.floor(index/8)*8);

def pos2index(pos):
    return pos[0] + pos[1]*8;

def str2index(str):
    return pos2index(str2pos(str));
    
def str2pos(str):
    return ((ord(str.upper()[0])-alphaValueOffset) % 8,int(str[1])-1);

def pos2str(pos):
    return chr( (pos[0]-alphaValueOffset) % 8).upper() + str(pos[1]+1);

    
class piece:
    pos = (0,0);
    board = None;
    team = -1;
    spritesheet = (pygame.image.load("chesspieces.png"),45);
    spriteIndex = (0,0);
    canRender = True;
    hadLastMove = False;
    hasMoved = False;
    validMoves = [];
    threat = [];
    semiThreat = [];
    char = ["?"];
    #Generell definisjon på en brikke
    def __init__(self,board,pos,team):
        self.pos = pos;
        self.team = team;
        self.board = board;
        self.hasMoved = False;
        self.threat = [];
        self.validMoves = [];
        self.semiThreat = [];
        self.hadLastMove = False;
        self.canRender = True;
        
    def render(self,surface):
        if(self.canRender):
            s = self.spritesheet;
            surface.blit(s[0],(self.pos[0]*s[1],self.pos[1]*s[1]),((self.spriteIndex[self.team]%6)*s[1],math.floor(self.spriteIndex[self.team]/6)*s[1],s[1],s[1]));
        
    def moveTo(self,pos):
        if(self.canMoveTo(pos)):
            self.hasMoved = True;
            p2 = self.board.getPieceAt(pos);
            self.board.setPieceAt(pos,self);
            self.board.setPieceAt(self.pos,None);
            self.pos = pos;
            if(p2):
                p2.kill();
                return True,True;
            return True,False;
        return False,False;
        
    def canMoveTo(self,pos):
        return pos in self.validMoves;
        '''if(self.board.firstEncounter(self.pos,pos) == pos):
            #if settning som ser om det er en brikke i mellom
            #brikkens posisjon og destinasjonen
            p2 = self.board.getPieceAt(pos);
            if(p2):
                return self.team != p2.team;
            return True;
        return False;'''
    
    def kill(self):
        #Logikk som skal kjøres når brikken blir slått ut
        pass;
        
    def update(self):
        self.validMoves = [];
        for i in self.threat:
            s = self.board.getPieceAt(i); 
            if((not s) or (s and s.team != self.team)):
                self.validMoves.append(i);
                
    def afterUpdate(self):
        pass;
    def __str__(self):
        return self.char[self.team%2];
        
class king(piece):
    char = ['K','k'];
    spriteIndex = (0,6);
    #Definisjon på hvordan kongen kan bevege seg
    def render(self,surface):
        if(self.board.isThreatend(self.pos,self.team)):
            pygame.draw.rect(surface,(255,100,0),(self.pos[0]*45,self.pos[1]*45,45,45));
        super(king,self).render(surface);
    
    def moveTo(self,pos):
        i2 = self.board.getPieceAt(pos);
        if(i2 and isinstance(i2,rook) and (not isinstance(i2,queen))):
            if(i2.canMoveTo(self.pos)):
                return i2.moveTo(self.pos);
            else:
                return False, False;
        else:
            return super(king,self).moveTo(pos);
            
    '''
    def canMoveTo(self,pos):
        i2 = self.board.getPieceAt(pos);
        if(i2 and isinstance(i2,rook) and (not isinstance(i2,queen))):
            return i2.canMoveTo(self.pos);
        return pos in self.validMoves;
        return super(king,self).canMoveTo(pos) and abs(pos[0]-self.pos[0]) <= 1 and (pos[1]-self.pos[1]) <= 1;
    '''
    def afterUpdate(self):
        threats = self.board.threatenedBy(self.pos,self.team);
        semi = self.board.threatenedBy(self.pos,self.team,True);
        vM = self.validMoves;
        self.validMoves = [];
        anyMove = False;
        for i in vM:
            '''
            if(not (self.board.isThreatend(i,self.team))):
                if(not (self.board.isThreatend(i,self.team,True))):
                self.validMoves += [i];
                anyMove = True;    
            '''
            tS = self.board.threatenedBy(i,self.team);
            
            if(len(tS) <= 0):
                sM = self.board.threatenedBy(i,self.team,True);
                if(len(sM)>0):
                    for k in sM:
                        if(not k in threats):
                            self.validMoves += [i];
                            break;
                else:
                    self.validMoves += [i];
        
        if(len(self.validMoves) > 0):
            anyMove=True;
        for i in self.board.board:
            if(i != self):
                if(i and i.team == self.team):
                    if(len(threats) == 1):
                        rC = self.board.raycast(self.pos,threats[0].pos);
                        vM = i.validMoves;
                        i.validMoves = [];
                        for j in vM:
                            if(j in rC):
                                i.validMoves += [j];
                    elif(len(threats) > 1):
                        i.validMoves = [];
                    elif(len(semi)>0):
                        for j in semi:
                            if(not len(i.validMoves)>0):
                                break;
                            if(i.pos in j.threat):
                                rCast = self.board.raycast(i.pos,j.pos);
                                vM = i.validMoves;
                                i.validMoves = [];
                                for v in vM:
                                    if((v in j.threat and v in rCast) or v==j.pos):
                                        i.validMoves += [v];
                    if(len(i.validMoves)>0):
                        anyMove = True;
        
        if(not anyMove):
            if(len(threats)>0):
                self.board.winner = ((self.team+1)%2);
            else:
                self.board.winner = 2;
    def update(self):
        s = self.pos;
        self.threat = [];
        self.validMoves = [];
        for i in range(9):
            nPos = (s[0]+(i%3)-1,s[1]+(int(i/3))-1);
            if(nPos == s or nPos[0] < 0 or nPos[1] < 0 or nPos[0] > 7 or nPos[1] > 7):
                continue;
            self.threat.append(nPos);
        super(king,self).update();
        if(not self.board.isThreatend(self.pos,self.team)):
            posT = [self.board.firstEncounter(self.pos,(self.pos[0]-8,self.pos[1])),
                    self.board.firstEncounter(self.pos,(self.pos[0]+8,self.pos[1]))];
            for p in posT:
                if(p):
                    i1 = self.board.getPieceAt(p);
                    if(i1):
                        i1.update();
                        if i1.canMoveTo(self.pos):
                            self.validMoves += [p];
        
                
class bishop(piece):
    char = ["B","b"];
    #Definisjon på hvordan løperen kan bevege seg
    spriteIndex = (2,6+2);
    '''
    def canMoveTo(self,pos):
        return super(bishop,self).canMoveTo(pos) and (
            abs(pos[0]-self.pos[0]) == abs(pos[1]-self.pos[1]));
    '''
    def update(self):
        self.threat = [];
        self.threat += self.board.raycast(self.pos,(self.pos[0]+8,self.pos[1]+8));
        self.threat += self.board.raycast(self.pos,(self.pos[0]-8,self.pos[1]+8));
        self.threat += self.board.raycast(self.pos,(self.pos[0]+8,self.pos[1]-8));
        self.threat += self.board.raycast(self.pos,(self.pos[0]-8,self.pos[1]-8));
        self.semiThreat = [];
        self.semiThreat += self.board.raycast(self.pos,(self.pos[0]+8,self.pos[1]+8),2);
        self.semiThreat += self.board.raycast(self.pos,(self.pos[0]-8,self.pos[1]+8),2);
        self.semiThreat += self.board.raycast(self.pos,(self.pos[0]+8,self.pos[1]-8),2);
        self.semiThreat += self.board.raycast(self.pos,(self.pos[0]-8,self.pos[1]-8),2);
        
        piece.update(self);
        
class rook(piece):
    char = ["R","r"];
    spriteIndex = (4,6+4);
    #Definisjon på hvordan tårnet kan bevege seg
    '''
    def moveTo(self,pos):
        i2 = self.board.getPieceAt(pos);
        if(i2 and isinstance(i2,king) and i2.team == self.team):
            if(self.canMoveTo(pos)):
                self.board.swapPieces(self.pos,pos);
                self.hasMoved = True;
                i2.hasMoved = True;
                return True,False;
        else:
            return super(rook,self).moveTo(pos);
        return False,False;
    '''
    def moveTo(self,pos):
        i2 = self.board.getPieceAt(pos);
        if(i2 and (not isinstance(self,queen)) and isinstance(i2,king) and i2.team == self.team):
            if(self.canMoveTo(pos)):
                
                nPosK = (int(i2.pos[0] + 2*math.copysign(1,self.pos[0]-i2.pos[0])),self.pos[1]);
                nPosS = (int(nPosK[0]+math.copysign(1,-self.pos[0]+i2.pos[0])),self.pos[1]);
                self.board.swapPieces(self.pos,nPosS);
                self.board.swapPieces(i2.pos,nPosK);
                self.pos = nPosS;
                i2.pos = nPosK;
                self.hasMoved = True;
                i2.hasMoved = True;
                return True, False;
        else:
            return super(rook,self).moveTo(pos);
        return False,False;
        
    '''
    def canMoveTo(self,pos):
        i2 = self.board.getPieceAt(pos);
        if(i2 and (not self.hasMoved) and isinstance(i2,king) 
          and (not i2.hasMoved) and i2.team == self.team
          and self.board.firstEncounter(self.pos,pos) == pos):
            return True;
            
            
        else:
            return super(rook,self).canMoveTo(pos) and (
                (abs(pos[0]-self.pos[0]) > 0) != (abs(pos[1]-self.pos[1]) > 0));
    '''
    def update(self):
        self.threat = [];
        self.threat += self.board.raycast(self.pos,(self.pos[0]+8,self.pos[1]));
        self.threat += self.board.raycast(self.pos,(self.pos[0]-8,self.pos[1]));
        self.threat += self.board.raycast(self.pos,(self.pos[0],self.pos[1]-8));
        self.threat += self.board.raycast(self.pos,(self.pos[0],self.pos[1]+8));
        self.semiThreat = [];
        self.semiThreat += self.board.raycast(self.pos,(self.pos[0]+8,self.pos[1]),2);
        self.semiThreat += self.board.raycast(self.pos,(self.pos[0]-8,self.pos[1]),2);
        self.semiThreat += self.board.raycast(self.pos,(self.pos[0],self.pos[1]-8),2);
        self.semiThreat += self.board.raycast(self.pos,(self.pos[0],self.pos[1]+8),2);
       
        piece.update(self);
        if((not self.hasMoved) and (not isinstance(self,queen))):
            p2 = self.board.firstEncounter(self.pos,(self.pos[0]+8,self.pos[1])) or self.board.firstEncounter(self.pos,(self.pos[0]-8,self.pos[1]))
            if(p2 and not self.board.isThreatend(p2,self.team)):
                i2 = self.board.getPieceAt(p2);
                if(i2 and isinstance(i2,king) and (not i2.hasMoved)):
                    tTest = self.board.raycast(p2,(p2[0] - 2*math.copysign(1,-self.pos[0]+p2[0]),p2[1]));
                    for i in tTest:
                        if(self.board.isThreatend(i,self.team)):
                            return;
                    self.validMoves += [p2];
        
class pawn(piece):
    char = ["P","p"];
    spriteIndex = (5,6+5);
    movedTwice = False;
    #Definisjon på hvordan bonden kan bevege seg
    #Bonden krever litt ekstra logikk, fordi den
    #har et spesialtrekk og kan bare slå ut andre
    #brikker på skrå
    def __init__(self,board,pos,team):
        piece.__init__(self,board,pos,team);
        self.movedTwice = False;
        
    def moveTo(self,pos):
        xDiff = -self.pos[0] + pos[0];
        yDiff = -self.pos[1] + pos[1];
        
        r,r2 = super(pawn,self).moveTo(pos);
        self.movedTwice = r and abs(yDiff) > 1;
        if(r and not r2 and abs(yDiff) == 1 and abs(xDiff) == 1):
            #If settning som sjekker om 'En passant', fjerner
            #motstanderen om det er tilfelle
            p2 = (pos[0],pos[1] + (self.team*2 - 1));
            i2 = self.board.getPieceAt(p2);
            self.board.setPieceAt(p2,None);
            i2.kill();
        if(r and ((pos[1]+1)%8) == self.team):
            #Sjekker om bonden har nådd enden av brettet
            while(True):
                try:
                    pieace_in = int(input("Change pawn to 1: queen, 2: knight, 3: bishop, 4: rook: "));
                    obj = queen(self.board,pos,self.team);
                    if(pieace_in == 2):
                        obj = knight(self.board,pos,self.team);
                    if(pieace_in == 3):
                        obj = bishop(self.board,pos,self.team);
                    if(pieace_in == 4):
                        obj = rook(self.board,pos,self.team);
                        
                    self.board.setPieceAt(pos,obj);
                    break;
                except Exception:
                    pass;
        return r,r2;
    
    def update(self):
        pos = self.pos;
        self.threat = [(pos[0]-1,pos[1]-(self.team*2 - 1)),(pos[0]+1,pos[1]-(self.team*2 - 1))];
        self.validMoves = [];
        
        for i in self.threat:
            p = self.board.getPieceAt(i);
            if(p and p.team != self.team):
                self.validMoves += [i];
        
        p1 = (pos[0],self.pos[1]-(self.team*2 - 1));
        p2 = (pos[0],self.pos[1]-(self.team*2 - 1)*2);
        
        if(not self.board.getPieceAt(p1)):
            self.validMoves += [p1];
        if(not self.hasMoved):
            if(not self.board.firstEncounter(pos,p2)):
                self.validMoves += [p2];
        
        p3 = (pos[0]-1,pos[1]);
        p4 = (pos[0]+1,pos[1]);
        i3 = self.board.getPieceAt(p3);
        i4 = self.board.getPieceAt(p4);
        
        if(i3 and i3.hadLastMove and isinstance(i3,pawn) and i3.movedTwice and i3.team != self.team):
            self.validMoves += [(pos[0]-1,pos[1]-(self.team*2 - 1))];
        elif(i4 and i4.hadLastMove and isinstance(i4,pawn) and i4.movedTwice and i4.team != self.team):
            self.validMoves += [(pos[0]+1,pos[1]-(self.team*2 - 1))];
    '''
    def canMoveTo(self,pos):
        
        if(super(pawn,self).canMoveTo(pos)):
            p2 = self.board.getPieceAt(pos);
            i2 = self.board.getPieceAt((pos[0],pos[1] + (self.team*2 - 1)))
            xDiff = -self.pos[0] + pos[0];
            yDiff = -self.pos[1] + pos[1];
            if(-yDiff == (self.team*2 - 1)):
                #Sjekker først om brikken beveger seg vertikalt og om det er
                #en brikke forran, så om det er mulig å utføre 'En passant'
                return xDiff == 0 and not(p2) or (
                    abs(xDiff)==1 and p2 or (i2 and isinstance(i2,pawn) and i2.movedTwice));
                    
            return ((-yDiff)/2) == (self.team*2-1) and not(self.hasMoved) and not p2;
        else:
            return False;'
        return pos in self.validMoves;
    '''
class knight(piece):
    char = ["N","n"];
    #Definisjon på hvordan springeren kan bevege seg
    spriteIndex = (3,6+3);
    '''
    def canMoveTo(self,pos):
        p2 = self.board.getPieceAt(pos);
        if((not p2) or (p2.team != self.team)):
            return (abs(self.pos[0]-pos[0]) == 2 and
                    abs(self.pos[1]-pos[1]) == 1) or (
                    abs(self.pos[1]-pos[1]) == 2 and
                    abs(self.pos[0]-pos[0]) == 1);
    '''
    def update(self):
        self.threat = [];
        cPos = [(self.pos[0]+2,self.pos[1]+1),
               (self.pos[0]+2,self.pos[1]-1),
               (self.pos[0]-2,self.pos[1]+1),
               (self.pos[0]-2,self.pos[1]-1),
               (self.pos[0]+1,self.pos[1]+2),
               (self.pos[0]+1,self.pos[1]-2),
               (self.pos[0]-1,self.pos[1]+2),
               (self.pos[0]-1,self.pos[1]-2)];
        
        for i in cPos:
            if(i[0] >= 0 and i[0] < 8 and i[1] < 8 and i[1] >= 0):
                self.threat.append(i);
                o = self.board.getPieceAt(i);
                
        super(knight,self).update();
        
class queen(rook,bishop):
    char = ["Q","q"];
    spriteIndex = (1,6+1);
    #Definisjon på hvordan dronningen kan bevege seg
    #gjør dette ved å la queen være en blanding av tårn og løper
    '''
    def canMoveTo(self,pos):
        return super(rook,self).canMoveTo(pos) or (
            super(bishop,self).canMoveTo(pos));
    '''
    
    def update(self):
        rook.update(self);
        a = self.threat;
        b = self.validMoves;
        c = self.semiThreat;
        bishop.update(self);
        self.threat += a;
        self.validMoves += b;
        self.semiThreat += c;
        
class chessboard:
    board = [None]*(8*8);
    currentTeam = 0;
    background = pygame.image.load("chessbg.png");
    winner = -1;
    lastPiece = None;
    #threatField brukes for å finne ut om 
    #brikker ved forkjellige felter er truet
    
    def __init__(self):
        #Setter alle feltene til None;
        self.board = [None]*(8*8);
        self.winner = -1;
        self.lastPiece = None;
        self.currentTeam = 0;
        pass;
        
    def testBoard(self):
        #Setter brettet til et test brett
        self.board[0:7] = [rook(self,(0,0),0),knight(self,(1,0),0),bishop(self,(2,0),0),queen(self,(3,0),0),
                           king(self,(4,0),0),bishop(self,(5,0),0),knight(self,(6,0),0),rook(self,(7,0),0)];
        self.board[8:15] = [pawn(self,(i,1),0) for i in range(8)];
        self.board[pos2index((1,3))] = pawn(self,(1,3),1);
        self.board[pos2index((3,3))] = queen(self,(3,3),1);
        pass;
        
    def regularBoard(self):
        #Setter brette opp for et klassisk spill
        self.board[0:7] = [rook(self,(0,0),0),knight(self,(1,0),0),bishop(self,(2,0),0),queen(self,(3,0),0),
                           king(self,(4,0),0),bishop(self,(5,0),0),knight(self,(6,0),0),rook(self,(7,0),0)];
        self.board[8:15] = [pawn(self,(i,1),0) for i in range(8)];
        
        self.board[pos2index((0,7))-1:pos2index((7,7))-1] = [rook(self,(0,7),1),knight(self,(1,7),1),bishop(self,(2,7),1),queen(self,(3,7),1),
                           king(self,(4,7),1),bishop(self,(5,7),1),knight(self,(6,7),1),rook(self,(7,7),1)];
        self.board[pos2index((0,6)):pos2index((7,6))] = [pawn(self,(i,6),1) for i in range(8)];
        
    
    def castelingTestBoard(self):
        self.board[0:7] = [rook(self,(0,0),0),None,None,None,
                           king(self,(4,0),0),None,None,rook(self,(7,0),0)];
        self.board[pos2index((0,7)):pos2index((7,7))-1] = [rook(self,(0,7),1),None,None,None,
                           queen(self,(4,7),1),None,None,rook(self,(7,7),1)];

    def updateAll(self):
        for i in self.board:
            if(i):
                i.update();
                
    def afterUpdate(self):
        for i in self.board:
            if(i):
                i.afterUpdate();
    
    def setBoard(self,board):
        #Setter brettet til board
        for i,v in enumerate(board):
            board[i] = v;
    
    def move(self,pos1,pos2):
        #Flytter brikke på posisjon 1 til posisjon 2
        if not(pos1 == pos2 and self.winner == -1):
            try:
                b1 = self.board[pos2index(pos1)];
                if(b1 and (b1.team == self.currentTeam or b1.team == -1)):
                    if(b1.moveTo(pos2)[0]):
                        if(self.lastPiece):
                            self.lastPiece.hadLastMove = False;
                        self.lastPiece = b1;
                        b1.hadLastMove = True;
                        self.currentTeam = (self.currentTeam + 1)%2;
                        self.updateAll();
                        self.updateAll();
                        self.afterUpdate();
                        if(self.winner != -1):
                            print("Game over!");
                            if(self.winner < 2):
                                print("The winner is {}".format(("white","black")[self.winner]));
                            else:
                                print("The game was a draw");
                        
                        return True;
                    else:
                        return False;
            except IndexError:
                return False;
        
    def setPieceAt(self,pos,piece):
        #Setter feltverdien til en brikker
        self.board[pos2index(pos)] = piece;
        
    def swapPieces(self,pos1,pos2):
        #Bytter om plassene til to brikker
        self.board[pos2index(pos1)],self.board[pos2index(pos2)] = self.board[pos2index(pos2)],self.board[pos2index(pos1)];
        
    def getPieceAt(self,pos):
        #Returnerer brikken i feltet
        return self.board[pos2index(pos)];
    
    def firstEncounter(self,pos,pos2,maxOcc=1):
        #Finner det første felted der en annen brikke er
        diffX = -pos[0]+pos2[0];
        diffY = -pos[1]+pos2[1];
        cPos = pos;
        first = True;
        
        for i in self.raycast(pos,pos2,maxOcc):
            if(self.getPieceAt(i)):
                return i;
      
    def threatenedBy(self,pos,team,semi=False):
        t = [];
        for i in self.board:
            if(i and i.team != team):
                if(semi and pos in i.semiThreat):
                    t += [i];
                elif(pos in i.threat):
                    t += [i];
        return t;
        
    def isThreatend(self,pos,team,semi=False):
        #Uoptimalisert måte å sjekke om et felt er truet
        for i in self.board:
            if(i and i.team != team):
                if(semi and pos in i.semiThreat):
                    return True;
                if(pos in i.threat):
                    return True;
                
        return False;
    def raycast(self,pos,pos2,maxocc = 1):
        #Returnerer alle cellene fra pos til pos2
        diffX = -pos[0]+pos2[0];
        diffY = -pos[1]+pos2[1];
        cPos = pos;
        cells = [];
        first = True;
        
        
        try:
            inc = diffY/diffX;
        except ZeroDivisionError:
            inc = "inf";
        
        for i in range(8):
            if(not first and self.getPieceAt((int(cPos[0]),int(cPos[1])))):
                maxocc-=1;

            if(cPos == pos2 or maxocc<=0):
                return cells;
            cPos = (cPos[0]+ (0 if inc == "inf" else math.copysign(1,diffX)),cPos[1] + (math.copysign(1,diffY) if inc=="inf" else inc*math.copysign(1,diffX)));
            if(not (cPos[0] < 0 or cPos[0] > 7 or cPos[1] < 0 or cPos[1] > 7)):
                cells.append((int(cPos[0]),int(cPos[1])));    
            else:
                return cells;
                    
            first = False;
        
    def renderBG(self,surface):
        surface.blit(self.background,(0,0),(0,0,360,360));
    
    def renderPieces(self,surface):
        for i in self.board:
            if(i):
                i.render(surface);
    
    def __str__(self):
        o = "   ";
        for i in range(8):
            o += " " + str(chr(i+alphaValueOffset));
        o+="\n";
        r=0;
        c=0;
        for i in range(8):
            o+= " "*3; 
            for j in range(8):
                r = math.ceil(i/8);
                c = math.ceil(j/8);
                o += boardfix[r][c] + "─";
            o+=boardfix[r][2] + "\n";
            o+=str(i+1) + " "*(2-(len(str(i+1))-1));
            for j in range(8):
                o+="|"+ (str(self.board[j + i*8] or " "));
            o+="|\n";
        o+= "   ";
        for j in range(8):
            c = math.ceil(j/8);
            o += boardfix[2][c] + "─";
        o+=boardfix[2][2] + "\n";
        return o;
        

def getMove():
    while(True):
        try:
            in1 = input("Next move: ").split(" ");
            p1 = str2pos(in1[0]);
            p2 = str2pos(in1[1]);
            return p1,p2;
        except Exception:
            print("Bad input");
            
def mainC():
    while(True):
        print(rGame);
        print("Current player: {}".format("black" if rGame.currentTeam else "white"));
        while(not rGame.move(*getMove())):
            pass;


def main():
    chessGame = chessboard();
    chessGame.regularBoard();
    chessGame.updateAll();
    chessGame.updateAll();
    chessGame.afterUpdate();
    screenSize = 360,360;
    display = pygame.display.set_mode(screenSize);
    pygame.display.set_caption("Sjakk");
    runGame = True;
    time = 0;
    clock = pygame.time.Clock();
    pieceInHand = None;
    mPos = (0,0);
    mOffset = (0,0);
    print(chessGame);
    while(runGame):
        mPos = pygame.mouse.get_pos();
        for event in pygame.event.get():
            if(event.type == pygame.QUIT):
                runGame = False;
            
            if(chessGame.winner == -1):
                if(event.type == 5):
                    #Mouse click
                    i1 = chessGame.getPieceAt((int(mPos[0]/45),int(mPos[1]/45)));
                    if(i1 and i1.team == chessGame.currentTeam):
                        mOffset = (int(mPos[0]%45),int(mPos[1]%45));
                        if(pieceInHand):
                            pieceInHand.canRender = True;
                        i1.canRender = False;
                        pieceInHand = i1;
                        #pieceInHand.update();
                        

            if(event.type == 6):
                if(pieceInHand):
                    if(chessGame.move(pieceInHand.pos,(int(mPos[0]/45),int(mPos[1]/45)))):
                        print(chessGame);
                        print("Current player: {}".format("black" if chessGame.currentTeam else "white"));
                    pieceInHand.canRender = True;
                    pieceInHand = None;
                    
        display.fill((0,0,0));
        
        chessGame.renderBG(display);
        if(pieceInHand):
            dPm = pieceInHand;
        else:
            dPm = chessGame.getPieceAt((int(mPos[0]/45),int(mPos[1]/45)));
        if(dPm and dPm.team == chessGame.currentTeam):
            for i in dPm.validMoves:
                cDiff = -100*((i[0]+1+i[1])%2);
                c = (0,255+cDiff,0);
                pAt=chessGame.getPieceAt(i);
                if(pAt):
                    if(pAt.team != dPm.team):
                        c = (255+cDiff,0,0);
                    else:
                        c = (0,0,255+cDiff);    
                pygame.draw.rect(display,c,(i[0]*45,i[1]*45,45,45));

        chessGame.renderPieces(display);
        if(pieceInHand):
            p = pieceInHand;
            s = pieceInHand.spritesheet;
            display.blit(s[0],(mPos[0]-mOffset[0],mPos[1]-mOffset[1]),((p.spriteIndex[p.team]%6)*s[1],math.floor(p.spriteIndex[p.team]/6)*s[1],s[1],s[1]));
        clock.tick(60);
        pygame.display.update();
        time+=0.1;
    
main();