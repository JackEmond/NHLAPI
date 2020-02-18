import requests
import datetime
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    #Get the date and convert it so that the 
    date = datetime.date.today().strftime("%Y-%m-%d")
    print(date)
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2018-01-02&endDate=2018-01-02'
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate='+ date +'&endDate=' + date
    json_data = requests.get(url).json() 
    
    #Create An array to store the data
    box_scores = []

    #Find Data in API and Store It So that it can be shown as box scores
    for each in json_data['dates'][0]['games']:
        box_scores.append([
                    #Home Team Stats
                    each['teams']['home']['team']['name'],                                  # Home Team Name {0}
                    each['teams']['home']['score'],                                         # Home Team Score {1}
                    each['teams']['home']['leagueRecord']['wins'],                          # Home Team Wins {2}
                    each['teams']['home']['leagueRecord']['losses'],                        # Home Team Losses {3}
                    each['teams']['home']['leagueRecord']['ot'],                            # Home Team OT Wins {4}
                    
                    #Away Team Stats
                    each['teams']['away']['team']['name'],                                  # Away Team Name {5}
                    each['teams']['away']['score'],                                         # Away Team Score {6}
                    each['teams']['away']['leagueRecord']['wins'],                          # Away Team Wins {7}
                    each['teams']['away']['leagueRecord']['losses'],                        # Away Team Losses {8}
                    each['teams']['away']['leagueRecord']['ot'],                            # Away Team OT Wins {9}
                    

                    each['gamePk'],                            # Game ID (to get game number) {10}
                    each['status']['abstractGameState'],       # Game Status (eg. Live/Preview/Final)  {11}

                   ])
   
    
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        box_scores = box_scores,
        year=datetime.date.today().strftime("%Y")
    )

@app.route('/gamestats/<gamePk>')
def gamestats(gamePk):
    
    #GET NHL API Data
    
    # Get single game API
    game_api = 'https://statsapi.web.nhl.com/api/v1/game/' + gamePk + '/feed/live'
    json_data = requests.get(game_api).json() 


    # Get home team api
    home_id = json_data['gameData']['teams']['home']['id']
    home_team_stats_api ='https://statsapi.web.nhl.com/api/v1/teams/' + str(home_id) + '?expand=team.stats'
    home_team_stats_json_data = requests.get(home_team_stats_api).json() 

     # Get away team api
    away_id = json_data['gameData']['teams']['away']['id']
    #away_team_stats_api ='https://statsapi.web.nhl.com/api/v1/schedule?teamId=' + str(away_id) 
    away_team_stats_api ='https://statsapi.web.nhl.com/api/v1/teams/' + str(away_id) + '?expand=team.stats'
    away_team_stats_json_data = requests.get(away_team_stats_api).json() 


  

    #Output home data
    hometeam = json_data['gameData']['teams']['home']['name']
    home_wins = home_team_stats_json_data['teams'][0]['teamStats'][0]['splits'][0]['stat']['wins']
    home_losses = home_team_stats_json_data['teams'][0]['teamStats'][0]['splits'][0]['stat']['losses']
    home_ot = home_team_stats_json_data['teams'][0]['teamStats'][0]['splits'][0]['stat']['ot']

    home_stats = '(' + str(home_wins) + ' - ' + str(home_losses)+ ' - ' + str(home_ot) + ')'

    #Output away data
    awayteam = json_data['gameData']['teams']['away']['name']

    #away_score = away_team_stats_json_data ['dates'][0]['games'][0]['teams']['away']['score']

    away_wins = away_team_stats_json_data['teams'][0]['teamStats'][0]['splits'][0]['stat']['wins']
    away_losses = away_team_stats_json_data['teams'][0]['teamStats'][0]['splits'][0]['stat']['losses']
    away_ot = away_team_stats_json_data['teams'][0]['teamStats'][0]['splits'][0]['stat']['ot']

    away_stats = '(' + str(away_wins) + ' - ' + str(away_losses)+ ' - ' + str(away_ot) + ')'

    #score =  str(home_score) + ' - ' + str(away_score)

    gamestate = json_data['gameData']['status']['abstractGameState']
    if gamestate != "Preview":
        gametime =  json_data['liveData']['plays']['allPlays'][len(json_data['liveData']['plays']['allPlays'])-1]['about']['periodTimeRemaining']
        gameperiod = json_data['liveData']['plays']['allPlays'][len(json_data['liveData']['plays']['allPlays'])-1]['about']['ordinalNum']
    else: 
        gameperiod = gamestate

    if gameperiod == 'Preview':
        time = json_data['gameData']['datetime']['dateTime']
        d = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
        hour = d.strftime('%I') 
        second = d.strftime(':%M')
        gamestate= str(int(hour) + 7) + second + 'PM'
    elif gameperiod == '3rd' and str(gametime) == '00:00':
        gamestate = 'FINAL'
    else:
        gamestate = str(gameperiod) + ' ' + str(gametime)


    home_player_stats = []
    home_goalie_stats = []
    for e in json_data['liveData']['boxscore']['teams']['home']['players']:
        if 'skaterStats' in json_data['liveData']['boxscore']['teams']['home']['players'][e]['stats']:
            home_player_stats.append([
                    # THe reason skaterstats doesnt work might be because goalies have goaliestats not skaterstats
                    json_data['liveData']['boxscore']['teams']['home']['players'][e]['person']['fullName'], 
                    json_data['liveData']['boxscore']['teams']['home']['players'][e]['stats']['skaterStats']['goals'], 
                    json_data['liveData']['boxscore']['teams']['home']['players'][e]['stats']['skaterStats']['assists'], 
                    json_data['liveData']['boxscore']['teams']['home']['players'][e]['stats']['skaterStats']['shots'], 
                   ])
        elif 'goalieStats' in json_data['liveData']['boxscore']['teams']['home']['players'][e]['stats']:
             
            saves = json_data['liveData']['boxscore']['teams']['home']['players'][e]['stats']['goalieStats']['saves'] 
            shots = json_data['liveData']['boxscore']['teams']['home']['players'][e]['stats']['goalieStats']['shots']
            if shots != 0 or saves != 0:
                save_percentage = saves / shots
            else:
                save_percentage = 0
            home_goalie_stats.append([
                    # THe reason skaterstats doesnt work might be because goalies have goaliestats not skaterstats
                    json_data['liveData']['boxscore']['teams']['home']['players'][e]['person']['fullName'], 
                    saves,
                    shots,
                    #.format makes it so its formatted to 3 decimal places if its less than 3 decimal places, round makes it so if the number has more than 3 decimal places it shows only 3 decimal places
                    "{0:.3f}".format(round(save_percentage, 3))

                   ])


    away_player_stats = []
    away_goalie_stats = []
    for i in json_data['liveData']['boxscore']['teams']['away']['players']:
        if 'skaterStats' in json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']:
            away_player_stats.append([
                    # THe reason skaterstats doesnt work might be because goalies have goaliestats not skaterstats
                    json_data['liveData']['boxscore']['teams']['away']['players'][i]['person']['fullName'], 
                    json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']['skaterStats']['goals'], 
                    json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']['skaterStats']['assists'], 
                    json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']['skaterStats']['shots'], 

                   ])
        elif 'goalieStats' in json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']:
             
            saves = json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']['goalieStats']['saves'] 
            shots = json_data['liveData']['boxscore']['teams']['away']['players'][i]['stats']['goalieStats']['shots']
            if shots != 0 or saves != 0:
                save_percentage = saves / shots
            else:
                save_percentage = 0
            away_goalie_stats.append([
                    # THe reason skaterstats doesnt work might be because goalies have goaliestats not skaterstats
                    json_data['liveData']['boxscore']['teams']['away']['players'][i]['person']['fullName'], 
                    saves,
                    shots,
                    #.format makes it so its formatted to 3 decimal places if its less than 3 decimal places, round makes it so if the number has more than 3 decimal places it shows only 3 decimal places
                    "{0:.3f}".format(round(save_percentage, 3))

                   ])

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
   
    #Game Stats
    

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
        home_stats = home_stats,
        away_stats = away_stats,
        #score = score,
        gamestate = gamestate,
        year=datetime.date.today().strftime("%Y")
    )

@app.route('/Contact')
def contact():
    return render_template(
        'contact.html',
        title='Contact Page',
        year=datetime.date.today().strftime("%Y")
    )



if(__name__) == '__main__':
    app.run(debug=True)