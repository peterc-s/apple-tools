<START> PRINT "NUMBER GUESSING GAME"
PRINT "I am thinking of a number from 1 to 10"

REM generate number from 1-10
<NEWGAME> N = INT(RND(1)*10)+1
PRINT
PRINT "Guess the number."

REM the main game loop
<GAMELOOP> INPUT "Your guess: ";G
W = 0
GOSUB @CHECKGUESS
IF W = 1 THEN @WIN
GOTO @GAMELOOP

REM checks where G is relative to N
<CHECKGUESS> IF G = N THEN @CORRECT
IF G < N THEN @LOW
IF G > N THEN @HIGH
RETURN

REM set win flag if correct
<CORRECT> W = 1
RETURN

<LOW> PRINT "TOO LOW"
RETURN

<HIGH> PRINT "TOO HIGH"
RETURN

<WIN> PRINT "CORRECT!"

REM fallthrough to gameover
<GAMEOVER> INPUT "Play again? (1=yes, 2=no): ";A
ON A GOTO @NEWGAME,@END
GOTO @GAMEOVER

<END> PRINT "Goodbye!"
END
