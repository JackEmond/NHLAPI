import requests
import datetime
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

def getGameStats(game_stat):
    gamestate = game_status(game_stat['gamePk'])
    return [
        #Home Team Stats
        game_stat['teams']['home']['team']['name'],                  # Home Team Name {0}
        game_stat['teams']['home']['score'],                         # Home Team Score {1}
        game_stat['teams']['home']['leagueRecord']['wins'],          # Home Team Wins {2}
        game_stat['teams']['home']['leagueRecord']['losses'],        # Home Team Losses {3}
        game_stat['teams']['home']['leagueRecord']['ot'],            # Home Team OT Wins {4}
        #Away Team Stats
        game_stat['teams']['away']['team']['name'],                  # Away Team Name {5}
        game_stat['teams']['away']['score'],                         # Away Team Score {6}
        game_stat['teams']['away']['leagueRecord']['wins'],          # Away Team Wins {7}
        game_stat['teams']['away']['leagueRecord']['losses'],        # Away Team Losses {8}
        game_stat['teams']['away']['leagueRecord']['ot'],            # Away Team OT Wins {9}

        game_stat['gamePk'], # Game ID (so when you click the game it goes to the gamestats page) {10}
        gamestate,       # Game Status (eg. Live/Preview/Final)  {11}
    ]

def getPlayerStats(json_data, location):
    player_stats = []
    goalie_stats = []

    for i in json_data['liveData']['boxscore']['teams'][location]['players']:
        player = json_data['liveData']['boxscore']['teams'][location]['players'][i]
        if 'skaterStats' in json_data['liveData']['boxscore']['teams'][location]['players'][i]['stats']:
            player_stats.append([
                    player['person']['fullName'], 
                    player['stats']['skaterStats']['goals'], 
                    player['stats']['skaterStats']['assists'], 
                    player['stats']['skaterStats']['shots'], 

                   ])
        elif 'goalieStats' in player['stats']:
            saves = player['stats']['goalieStats']['saves'] 
            shots = player['stats']['goalieStats']['shots']
            if shots != 0 or saves != 0:
                save_percentage = saves / shots
            else:
                save_percentage = 0

            goalie_stats.append([
                   player['person']['fullName'], 
                    saves,
                    shots,
                    #.format to 3 decimal if more or less than 3 decimals
                    "{0:.3f}".format(round(save_percentage, 3))

                   ])
    return player_stats, goalie_stats

def getHighlights(gamePk):
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
    return highlights_data

#Home Page
@app.route('/')
def index():
    #Get the date and convert it so that the api is able to grab all games occuring today
    date = datetime.date.today().strftime("%Y-%m-%d")
    #uncomment below to show gamedata for that specific date. Used for testing purposes
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2017-04-06&endDate=2017-04-06'
    #url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate='+ date +'&endDate=' + date
    live_games = requests.get(url).json() 
    
    their_are_games_today = 'yes'

    #Find Each teams name, goals_scored, and record for all games occuring today
    if not live_games:
        url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2017-04-06&endDate=2017-04-06'
        live_games = requests.get(url).json() 
        their_are_games_today = 'no'
    
    list_of_games = []

    for game_data in live_games['dates'][0]['games']:
        singleGameStats = getGameStats(game_data)
        list_of_games.append(singleGameStats)
        
        
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        game_stats = list_of_games,
        their_are_games_today = their_are_games_today,
        year=datetime.date.today().strftime("%Y")
    )

def sortPlayerStats(player_stats):
    player_stats.sort(key=lambda x:(x[1], x[2], x[3]))
    player_stats.reverse()
    return player_stats

# Individual Game Page
@app.route('/gamestats/<gamePk>')
def gamestats(gamePk):
    
    #GET NHL API Data
    date = datetime.date.today().strftime("%Y-%m-%d")
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2017-04-06&endDate=2017-04-06'
    #url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate='+ date +'&endDate=' + date
    live_games = requests.get(url).json() 
    
    if not live_games:
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
            break


    # Get single game API
    game_api = 'https://statsapi.web.nhl.com/api/v1/game/' + gamePk + '/feed/live'
    json_data = requests.get(game_api).json() 


    gamestate = game_status(gamePk)

    #Get Home Player / Goalies Stats
    home_player_stats, home_goalie_stats = getPlayerStats(json_data, 'home')
    home_player_stats = sortPlayerStats(home_player_stats)


    #Get Away Player / Goalies Stat
    away_player_stats, away_goalie_stats = getPlayerStats(json_data, 'away')
    away_player_stats = sortPlayerStats(away_player_stats)

    #Highlights
    highlights = getHighlights(gamePk)
    

    return render_template(
        'gamestats.html',
        title='Game Stats',
        away_player_stats = away_player_stats,
        away_goalie_stats = away_goalie_stats,
        home_player_stats = home_player_stats,
        home_goalie_stats = home_goalie_stats,
        highlights_data = highlights,
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




