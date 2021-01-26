import requests
import datetime
import json
import dateutil.parser
from flask import Flask, render_template
from datetime import datetime as dt

app = Flask(__name__)
'''
Function that passes the game id number and returns the game state
if the game hasnt started the game start time is returned
if the game has started the period and how much time is remaining in the period is returned
if the game is over Final is returned
This is called twice. Once on the home page, and once on the individual game page
'''
def game_status(gameid):
    #rename determine_game_state

    #Determine the state of the game (Preview/Live/Finished)
    json_game_id = 'https://statsapi.web.nhl.com/api/v1/game/' + str(gameid) + '/feed/live'
    json_data = requests.get(json_game_id).json() 
    gamestate = json_data['gameData']['status']['abstractGameState']
    
    if gamestate == 'Preview': #game has not started. Return when it starts
        time = json_data['gameData']['datetime']['dateTime']
        d = dt.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
        # time is in grenwich mean time. Therefore convert it to est
        hour = int(d.strftime('%I')) + 7 
        second = d.strftime(':%M')

        # If in military time remove 12 hours 
        if hour >= 13:
            return str(hour - 12) + second + 'PM'
        else:
            return str(hour) + second + 'PM'

    elif gamestate == 'Final': 
        return 'FINAL'
    else: #game is live. Return what period and how much time is left
        gametime =  json_data['liveData']['plays']['allPlays'][len(json_data['liveData']['plays']['allPlays'])-1]['about']['periodTimeRemaining']
        gameperiod = json_data['liveData']['plays']['allPlays'][len(json_data['liveData']['plays']['allPlays'])-1]['about']['ordinalNum']
        return str(gameperiod) + ' ' + str(gametime)
    #end of function

#Home Page
@app.route('/')
def index():
    #Get the date and convert it so that the api is able to grab all games occuring today
    date = datetime.date.today().strftime("%Y-%m-%d")
    #uncomment below to show gamedata for that specific date. Used for testing purposes
    #url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2018-01-02&endDate=2018-01-02'
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate='+ date +'&endDate=' + date
    json_data = requests.get(url)
    live_games = json.loads(json_data.text)

    game_stats = []
    are_their_games_today = 'yes'
<<<<<<< HEAD
    
    #if their are no games today instead show dummy data
    if not live_games:
        url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2019-02-02&endDate=2019-02-02'
=======

    #Find Each teams name, goals_scored, and record for all games occuring today
    if live_games:
        url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2017-04-06&endDate=2017-04-06'
>>>>>>> 4ce016428d8445ae3b6e6ae578b501c281e079e5
        live_games = requests.get(url).json() 
        are_their_games_today = 'no'
    
    for game_stat in live_games['dates'][0]['games']:
        gamestate = game_status(game_stat['gamePk'])
        single_game_stats = {
             #Home Team Stats
            'Home Team Name' : game_stat['teams']['home']['team']['name'],                  # Home Team Name {0}
            'Home Team Score' : game_stat['teams']['home']['score'],                         # Home Team Score {1}
            'Home Team Wins' : game_stat['teams']['home']['leagueRecord']['wins'],          # Home Team Wins {2}
            'Home Team Losses' : game_stat['teams']['home']['leagueRecord']['losses'],        # Home Team Losses {3}
            'Home Team OT' : game_stat['teams']['home']['leagueRecord']['ot'],            # Home Team OT Wins {4}
            
            #Away Team Stats
            'Away Team Name' : game_stat['teams']['away']['team']['name'],                  # Away Team Name {5}
            'Away Team Score' : game_stat['teams']['away']['score'],                         # Away Team Score {6}
            'Away Team Wins' : game_stat['teams']['away']['leagueRecord']['wins'],          # Away Team Wins {7}
            'Away Team Losses' : game_stat['teams']['away']['leagueRecord']['losses'],        # Away Team Losses {8}
            'Away Team OT' : game_stat['teams']['away']['leagueRecord']['ot'],            # Away Team OT Wins {9}

            'Game ID' : game_stat['gamePk'],                            # Game ID (so when you click the game it goes to the gamestats page) {10}
            'Game State' : gamestate,       # G
        }
        game_stats.append(single_game_stats)


    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        game_stats = game_stats,
        are_their_games_today = are_their_games_today,
        year=datetime.date.today().strftime("%Y")
    )


# Individual Game Page
@app.route('/gamestats/<gamePk>')
def gamestats(gamePk):
    
    #GET NHL API Data
    date = datetime.date.today().strftime("%Y-%m-%d")
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate='+ date +'&endDate=' + date
    live_games = requests.get(url).json() 
    
    if live_games:
        url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2017-04-06&endDate=2017-04-06'
        live_games = requests.get(url).json() 


    for game_stat in live_games['dates'][0]['games']:
        if str(game_stat['gamePk']) == gamePk:
            #homestats
            hometeam = game_stat['teams']['home']['team']['name']                  # Home Team Name
            home_wins = game_stat['teams']['home']['leagueRecord']['wins']         # Home Team Wins 
            home_losses = game_stat['teams']['home']['leagueRecord']['losses']        # Home Team Losses
            home_ot= game_stat['teams']['home']['leagueRecord']['ot']          # Home Team OT Wins
            home_score = game_stat['teams']['home']['score']
            #awaystats
            awayteam = game_stat['teams']['away']['team']['name']                 # Away Team Name 
            away_wins = game_stat['teams']['away']['leagueRecord']['wins']         # Away Team Wins 
            away_losses = game_stat['teams']['away']['leagueRecord']['losses']        # Away Team Losses 
            away_ot = game_stat['teams']['away']['leagueRecord']['ot']
            away_score = game_stat['teams']['away']['score']


    # Get single game API
    game_api = 'https://statsapi.web.nhl.com/api/v1/game/' + gamePk + '/feed/live'
    json_data = requests.get(game_api).json() 

    gamestate = game_status(gamePk)

    home_player_stats = []
    home_goalie_stats = []
    
    home_data = json_data['liveData']['boxscore']['teams']['home']['players']
    for e in home_data:
        if 'skaterStats' in home_data[e]['stats']:
            home_player_stats.append([
                    home_data[e]['person']['fullName'], 
                    home_data[e]['stats']['skaterStats']['goals'], 
                    home_data[e]['stats']['skaterStats']['assists'], 
                    home_data[e]['stats']['skaterStats']['shots'], 
                   ])
        elif 'goalieStats' in home_data[e]['stats']:
            saves = home_data[e]['stats']['goalieStats']['saves'] 
            shots = home_data[e]['stats']['goalieStats']['shots']
            if shots != 0 or saves != 0:
                save_percentage = saves / shots
            else:
                save_percentage = 0
            home_goalie_stats.append([
                    home_data[e]['person']['fullName'], 
                    saves,
                    shots,
                    #makes it so it always has 3 decimal places 
                    "{0:.3f}".format(round(save_percentage, 3))
                   ])

    home_player_stats.sort(key=lambda x:(x[1], x[2], x[3]))
    home_player_stats.reverse()

    away_player_stats = []
    away_goalie_stats = []

    for i in json_data['liveData']['boxscore']['teams']['away']['players']:
        away_player = json_data['liveData']['boxscore']['teams']['away']['players'][i]
        if 'skaterStats' in json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']:
            away_player_stats.append([
                    away_player['person']['fullName'], 
                    away_player['stats']['skaterStats']['goals'], 
                    away_player['stats']['skaterStats']['assists'], 
                    away_player['stats']['skaterStats']['shots'], 

                   ])
        elif 'goalieStats' in away_player['stats']:
            saves = away_player['stats']['goalieStats']['saves'] 
            shots = away_player['stats']['goalieStats']['shots']
            if shots != 0 or saves != 0:
                save_percentage = saves / shots
            else:
                save_percentage = 0

            away_goalie_stats.append([
                   away_player['person']['fullName'], 
                    saves,
                    shots,
                    #.format makes it so its formatted to 3 decimal places if its less than 3 decimal places, round makes it so if the number has more than 3 decimal places it shows only 3 decimal places
                    "{0:.3f}".format(round(save_percentage, 3))

                   ])

    away_player_stats.sort(key=lambda x:(x[1], x[2], x[3]))
    away_player_stats.reverse()

    #Highlights

    #Get Highlights api
    highlights_api = 'https://statsapi.web.nhl.com/api/v1/game/' + gamePk + '/boxscore'
    highlights_json_data = requests.get(highlights_api).json() 

    highlights_data = []
    highlights_data.append([
                    #Home Team Stats
                    highlights_json_data['teams']['home']['teamStats']['teamSkaterStats']['shots'],                         
                    highlights_json_data['teams']['home']['teamStats']['teamSkaterStats']['powerPlayPercentage'] ,               
                    highlights_json_data['teams']['home']['teamStats']['teamSkaterStats']['hits'],                           

                    highlights_json_data['teams']['away']['teamStats']['teamSkaterStats']['shots'],                         
                    highlights_json_data['teams']['away']['teamStats']['teamSkaterStats']['powerPlayPercentage'] ,                
                    highlights_json_data['teams']['away']['teamStats']['teamSkaterStats']['hits'],                          


                   ])
   

    return render_template(
        'gamestats.html',
        title='Game Stats',
        away_player_stats = away_player_stats,
        away_goalie_stats = away_goalie_stats,
        home_player_stats = home_player_stats,
        home_goalie_stats = home_goalie_stats,
        highlights_data = highlights_data,
        awayteam = awayteam,
        hometeam = hometeam,
        home_score = home_score,
        home_stats = '(' + str(home_wins) + ' - ' + str(home_losses)+ ' - ' + str(home_ot) + ')',
        away_score = away_score,
        away_stats = '(' + str(away_wins) + ' - ' + str(away_losses)+ ' - ' + str(away_ot) + ')',
        #score = score,
        gamestate = gamestate,
        year=datetime.date.today().strftime("%Y")
    )


if(__name__) == '__main__':
    app.run(debug=True)
