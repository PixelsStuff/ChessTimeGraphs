import requests
from datetime import datetime, timedelta
import re
import matplotlib.pyplot as plt

 # SETTINGS:

user = 'Wins' #seems pretty self explanatory 
monthsago = '3' #takes games from this amount of time long ago. MUST BE A INT
thetime_control = '600' #600 for 10 minute rapid, 300 for 5 minute blitz, 60 for 1 minute bullet. 

# OR: SEE LINES 216-217 
# ----- #




logging = 2
def get_remaining_times(pgn):
    # I used chatgpt for this regex. Too much.  
    time_pattern = re.compile(r"\[%clk (\d+:\d+:\d+(\.\d+)?)\]")
    white_pattern = re.compile(r'\[White "(.*?)"\]')
    black_pattern = re.compile(r'\[Black "(.*?)"\]')
    # Extract usernames
    white_username = white_pattern.search(pgn).group(1)
    black_username = black_pattern.search(pgn).group(1)
    move_times = [match.group(1) for match in time_pattern.finditer(pgn)]
    
    def to_seconds(time_str):
        fmt = '%H:%M:%S.%f' if '.' in time_str else '%H:%M:%S'
        time_delta = datetime.strptime(time_str, fmt) - datetime.strptime("0:0:0", '%H:%M:%S')
        return time_delta.total_seconds()
    
    parsed_times = [to_seconds(time) for time in move_times]
    white_times = parsed_times[0::2]  # White moves 
    black_times = parsed_times[1::2]  # Black moves
    
    return (white_times, black_times, white_username, black_username)
def getgames(username, monthspast, useragent='Wins'):
    """
    Fetch games of a Chess.com user going back a specified number of months from the current month.

    Parameters:
    - username (str): The Chess.com username.
    - monthspast (int): The number of months to go back from the current month.
    - headers (dict, optional): Optional headers to include in the request.

    Returns:
    - list: A list of PGN strings for the fetched games.
    """
    games_list = []
    
    
    now = datetime.now()
    year, month = now.year, now.month

    # Chess.com's API requires a user-agent
    if useragent is None:
        headers = {
            "User-Agent": "unknown"
        }
    else:
        headers = {
            "User-Agent": str(useragent)
        }
        
    for i in range(monthspast):
        if len(str(month)) == 1:
            month = '0' + str(month)
        print(month,year)
        url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month}"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an error for HTTP errors
            games_data = response.json()
            for game in games_data.get("games", []):
                try:
                    games_list.append(game["pgn"])
                except:
                    print("One game failed to load")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred for {year}-{month}: {e}")
            break  
        month = int(month)
        month -= 1
        if month <= 0:
            year -= 1
            month = 12
        
            
    return games_list
def get_timeandusers_pgn(pgn):
    # Regular expressions to match move times and usernames - Chatgpt 
    time_pattern = re.compile(r"\[%clk (\d+:\d+:\d+(\.\d+)?)\]")
    white_pattern = re.compile(r'\[White "(.*?)"\]')
    black_pattern = re.compile(r'\[Black "(.*?)"\]')    
    white_username = white_pattern.search(pgn).group(1)
    black_username = black_pattern.search(pgn).group(1)
    times = [match.group(1) for match in time_pattern.finditer(pgn)]
    
    def to_timedelta(time_str):
        fmt = '%H:%M:%S.%f' if '.' in time_str else '%H:%M:%S'
        return datetime.strptime(time_str, fmt) - datetime.strptime("0:0:0", '%H:%M:%S')
    
    times = [to_timedelta(time) for time in times]
    time_used_per_move = [(times[i] - times[i + 1]).total_seconds() for i in range(len(times) - 1)]
    
    white_times = time_used_per_move[0::2]  # even indices
    black_times = time_used_per_move[1::2]  # odd indices
    
    return (white_times, black_times, white_username, black_username)
def gettargetTandU(target,info):
    if target.lower() == info[2].lower():
        ttimes = info[0]
        if logging == 1:
            print('User',target,'is playing white')
    elif target.lower() == info[3].lower():
        ttimes = info[1]
        if logging == 1:
            print('User',target,'is playing black')
    else:
        print("User not found")
    return ttimes
def getaverages(allpgns,target,mode='avg'): #Modes are avg and times
    alltimes = []
    movestimes = {}
    movesamounts = {}
    moveaverages = {}
    failed_to_load = 0
    loaded = 0
    for pgn in allpgns:

        if mode == 'avg':
            try:
                pgn = get_timeandusers_pgn(pgn)
                #print('Got times',pgn)
                alltimes.append(gettargetTandU(target,pgn))
                loaded += 1
            except:
                failed_to_load += 1
                print('One game failed to load')

        if mode == 'times':
            try:
                pgn = get_remaining_times(pgn)
                #print('Got times',pgn)
                alltimes.append(gettargetTandU(target,pgn))
                loaded += 1
            except:
                failed_to_load += 1
                print('One game failed to load')
        
    print(loaded,"games loaded")
    print("total of",failed_to_load,"games failed to load")
    for game in alltimes:
        for i in range(len(game)):
            if i not in movestimes:
                movestimes[i] = game[i]
                movesamounts[i] = 1
            else:
                movestimes[i] += game[i]
                movesamounts[i] += 1
    
    Lmovestimes = list(movestimes.keys())
    for item in Lmovestimes:
        moveaverages[item] = abs(float(movestimes[item])/movesamounts[item])
        if logging > 1:
            if mode == 'avg':
                print("Average time spent on move",item-1,"is",moveaverages[item],"from",movestimes[item],"/",movesamounts[item])
            if mode == 'times':
                print("Average time left on move",item-1,"is",moveaverages[item],"from",movestimes[item],"in",movesamounts[item],'games')
    return moveaverages
def plot_points(x_values, y_values,x_name='X',y_name="Y",title='Title'):
    # Check if the lengths of x and y values match
    if len(x_values) != len(y_values):
        raise ValueError("The lists x_values and y_values must have the same length.")
    
    # Create the plot
    plt.plot(x_values, y_values, marker='o', linestyle='-', color='b')
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.title(title)
    
    # Show the plot
    plt.show()
def graphtimeused(player,timeago=6,timecontrol=600):
    games = (getgames(player,timeago))
    games = filterbytc(games,timecontrol)
    getaveragesresult = getaverages(games,player)
    xs = list(getaveragesresult.keys())
    ys = list(getaveragesresult.values())
    plot_points(xs,ys,"Move #","Avg. Time spent(s)",("Avg Time spent/move for: "+str(player)))

def graphtimeremaining(player,timeago=6,timecontrol=600):
    games = (getgames(player,timeago))
    games = filterbytc(games,timecontrol)
    getaveragesresult = getaverages(games,player,'times')
    xs = list(getaveragesresult.keys())
    ys = list(getaveragesresult.values())
    plot_points(xs,ys,"Move #","Avg. Time left(s)",("Avg Time remaining/move for: "+str(player)))
def get_time_control_and_result(pgn_text):
    time_control_match = re.search(r'\[TimeControl "(.*?)"\]', pgn_text)
    time_control = time_control_match.group(1) if time_control_match else "Unknown"
    result_match = re.search(r'\[Result "(.*?)"\]', pgn_text)
    result = result_match.group(1) if result_match else "Unknown"

    return time_control, result
def filterbytc(pgns,tc):
    returning = []
    for pgn in pgns:
        try:
            if get_time_control_and_result(pgn)[0] == str(tc):
                returning.append(pgn)
        except:
            print("One game failed to filter")
    return returning


graphtimeused(user,int(monthsago),thetime_control)
graphtimeremaining(user,int(monthsago),thetime_control)

