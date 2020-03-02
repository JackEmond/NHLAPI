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
    
    if gamestate == 'Preview': #game has not started
        time = json_data['gameData']['datetime']['dateTime']
        print(time)
        d = dt.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
        # time is in grenwich mean time. Therefore convert it to est
        hour = int(d.strftime('%I')) + 7 
        second = d.strftime(':%M')

        # If in military time remove 12 hours 
        if hour >= 13:
            return str(hour - 12) + second + 'PM'
        else:
            return str(hour) + second + 'PM'

    elif gamestate == 'Final': #game is over
        return 'FINAL'
    else: #game is live
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
    live_games = requests.get(url).json() 
    
    #Create An array to store the data
    game_stats = []

    #Find Each teams name, goals_scored, and record for all games occuring today
    for game_stat in live_games['dates'][0]['games']:
        gamestate = game_status(game_stat['gamePk'])
        game_stats.append([
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

                    game_stat['gamePk'],                            # Game ID (so when you click the game it goes to the gamestats page) {10}
                    gamestate,       # Game Status (eg. Live/Preview/Final)  {11}
                   ])
        

    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        game_stats = game_stats,
        year=datetime.date.today().strftime("%Y")
    )

# Individual Game Page
@app.route('/gamestats/<gamePk>')
def gamestats(gamePk):
    
    #GET NHL API Data
    
    # Get single game API
    game_api = 'https://statsapi.web.nhl.com/api/v1/game/' + gamePk + '/feed/live'
    json_data = requests.get(game_api).json() 

    # Get home team api
    home_id = json_data['gameData']['teams']['home']['id']
    home_team_stats_api ='https://statsapi.web.nhl.com/api/v1/teams/' + str(home_id) + '?expand=team.stats'
    home_team_stats_json_data = requests.get(home_team_stats_api).json()['teams'][0]['teamStats'][0]['splits'][0]['stat']

     # Get away team api
    away_id = json_data['gameData']['teams']['away']['id']
    #away_team_stats_api ='https://statsapi.web.nhl.com/api/v1/schedule?teamId=' + str(away_id) 
    away_team_stats_api ='https://statsapi.web.nhl.com/api/v1/teams/' + str(away_id) + '?expand=team.stats'
    away_team_stats_json_data = requests.get(away_team_stats_api).json() 

    #Output home data
    hometeam = json_data['gameData']['teams']['home']['name']
    home_wins = home_team_stats_json_data['wins']
    home_losses = home_team_stats_json_data['losses']
    home_ot = home_team_stats_json_data['ot']

    home_stats = '(' + str(home_wins) + ' - ' + str(home_losses)+ ' - ' + str(home_ot) + ')'

    #Output away data
    awayteam = json_data['gameData']['teams']['away']['name']

    away_team_stats = away_team_stats_json_data['teams'][0]['teamStats'][0]['splits'][0]['stat']
    away_wins = away_team_stats['wins']
    away_losses = away_team_stats['losses']
    away_ot = away_team_stats['ot']

    away_stats = '(' + str(away_wins) + ' - ' + str(away_losses)+ ' - ' + str(away_ot) + ')'

    gamestate = game_status(gamePk)

    home_player_stats = []
    home_goalie_stats = []
    home_score = 0
    home_data = json_data['liveData']['boxscore']['teams']['home']['players']
    for e in home_data:
        if 'skaterStats' in home_data[e]['stats']:
            home_score += home_data[e]['stats']['skaterStats']['goals']
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
    away_score = 0

    for i in json_data['liveData']['boxscore']['teams']['away']['players']:
        away_player = json_data['liveData']['boxscore']['teams']['away']['players'][i]
        if 'skaterStats' in json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']:
            away_score += away_player['stats']['skaterStats']['goals']
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
        home_stats = home_stats,
        away_score = away_score,
        away_stats = away_stats,
        #score = score,
        gamestate = gamestate,
        year=datetime.date.today().strftime("%Y")
    )


if(__name__) == '__main__':
    app.run(debug=True)
