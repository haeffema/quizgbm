# QUIZGBM

The bot sends the players a question everyday and checks there answers, after a set amount of wrong answers the player gets a hint and less points for the correct answer.
The quiz owner gets all answers from each player sent as dm and there is a log after a question is finished.

The design of the log is not final yet.

### Commands

The commands are in german but could easily be changed in english.

#### /start

Starts the quiz -> can only be used by the owner.

#### /beitreten

A player joins the quiz.

#### /benutzernamen_updaten

A player can change his/her nickname shown in the table.

#### /nachricht

The owner can send a message as the bot into the quiz channel.

#### /hinweis

If a player is not finished yet -> sends them the next hint and reduces der points by one.

If a player is finished -> sends them all hints in case they want to see them.

### Usage

#### Create .env file

TOKEN -> the token of your discord bot
OWNER_ID -> the discord id of the owner (the one who created the quiz)
QUIZ_CHANNEL_ID -> channel where the questions are sent to as well as dms
TABLE_CHANNEL_ID -> channel where the table is sent (its an image for better readability on mobile)
LOG_CHANNEL_ID -> channel where the question and all answers are shown once there is a new question
QUIZ_FOLDER -> the name of the folder of the active quiz

#### Adjust the time of question and reminder

in the consts.py edit quiz and reminder time, this transfers to the local time of the machine that is running the discord bot.

#### Run the bot

pip install -r requirements.txt

There are scripts for my personal linux machine, you need to change them for your own purposes.
Once the bot as run there will be a data.db file in the quiz folder. Here you'll need to add questions in the question table and edit the start and end message in the data table.

After thats done you can start the quiz with /start. Players can join before you've started.
