Go Game implementation based on Deepmind's AlphGozero!
# Game Rules
 <br />
The game is time-limited up to 30 minutes where each player’s timer starts with 15
minutes. The thinking time of a certain side is only decremented during his turn. The
computer is allowed to think/prepare during the other side’s turn and its timer will not be
decremented. When a side runs out of time, they automatically lose the game.
In this project, we will use a modified version of the Chinese rules. The rules are as
follows: <br />

1- The game is played on a board of size 19x19. A 19x19 board contains 19 vertical
lines and 19 horizontal lines. The intersection points between the lines are called
“Points”. Stones can only be placed on points. Figure.1 shows an example of a board. <br />
2- “Liberties” are used to denote the number of empty points around a certain stone. Stones in the middle of the board can have up to 4 liberties while stones on the edge
can have only 3 and stones in the corner can have only 2. Diagonal points are not taken
into account while calculating liberties.  <br />
3- The liberties for a group of stones is the sum of liberties of the stones in the group. A
group with zero liberties cannot exist on the board.  <br />
4- Initially, the board is empty, there are no prisoners on any side and each player has
an infinite supply of stones.  <br />
5- In Go, the black player starts playing first.  <br />
6- During their turn, each player can do one of the following moves: <br />
a) Resign: the player can resign from the game in which case the other player is
automatically declared as a winner. <br />
b) Pass: the player can pass his turn by surrendering one of his unplaced stones
to the opponent. <br />
c) Place a stone: the player can place a stone on any empty point as long as it
does not break any of the validity rules that will be described later.  <br /> <br />
7- If a player places a stone, the liberties of opponent groups are calculated and any group that has zero liberties is captured and its stones are added to the player’s prisoners. If no opponent group is captured, the liberties of the player’s group are calculated and if any group has no liberties, this move is considered a “Suicide” and it is invalidated.  <br />
8- To prevent infinite loops in the game, we will use the “Super Ko” rule to prevent
returning to any previous state. A state is defined by the current player’s color and the
board configuration. Therefore, two states with the same board configuration but
different current player are considered to be different. This rule is not applied to pass
moves. <br />
9- If the two players pass their turns in two consecutive turns, the game ends and the
scores are calculated to determine the winner.  <br />
10- After the game ends, each player’s score is calculated by counting their stones on
the board, the points in their territories and the prisoners they captured. The white player
get additional points called “Komi” added to his score which will be 6.5 in our competition.  <br />
11- The player with the higher score wins.  <br />
12- Unlike the Chinese rules, we do not remove dead stones from the board before
scoring and territory calculation.  <br />
13- A territory of a certain player is an area of empty points that is completely
surrounded by the stones of that player only. Any empty area that touches stones of
more than one color is not considered a territory. <br />
