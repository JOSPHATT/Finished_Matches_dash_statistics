import pandas as pd
import plotly.express as px
import os

def generate_dashboard():
    data_url = 'https://raw.githubusercontent.com/JOSPHATT/Finished_Matches/refs/heads/main/Finished_matches.csv'
    df = pd.read_csv(data_url)

    # Data preparation
    df = df.drop_duplicates()
    df_numeric = df.select_dtypes(include=['float64', 'int64'])
    df[df_numeric.columns] = df_numeric.fillna(df_numeric.median())
    df_categorical = df.select_dtypes(include=['object'])
    for col in df_categorical.columns:
        df[col] = df[col].fillna(df[col].mode()[0])

    if 'H_GOALS' in df.columns and 'A_GOALS' in df.columns:
        df['home_team_goal'] = df['H_GOALS']
        df['away_team_goal'] = df['A_GOALS']

    home_df = df[['HOME', 'home_team_goal', 'away_team_goal']].copy()
    home_df.columns = ['TEAM', 'goals_for', 'goals_against']
    home_df['matches_played'] = 1
    home_df['matches_won'] = (home_df['goals_for'] > home_df['goals_against']).astype(int)
    home_df['matches_drawn'] = (home_df['goals_for'] == home_df['goals_against']).astype(int)
    home_df['matches_lost'] = (home_df['goals_for'] < home_df['goals_against']).astype(int)

    away_df = df[['AWAY', 'away_team_goal', 'home_team_goal']].copy()
    away_df.columns = ['TEAM', 'goals_for', 'goals_against']
    away_df['matches_played'] = 1
    away_df['matches_won'] = (away_df['goals_for'] > away_df['goals_against']).astype(int)
    away_df['matches_drawn'] = (away_df['goals_for'] == away_df['goals_against']).astype(int)
    away_df['matches_lost'] = (away_df['goals_for'] < away_df['goals_against']).astype(int)

    team_df = pd.concat([home_df, away_df])
    team_stats = team_df.groupby('TEAM').sum().reset_index()
    team_stats['goal_difference'] = team_stats['goals_for'] - team_stats['goals_against']
    team_stats['goals_scored_per_match'] = team_stats['goals_for'] / team_stats['matches_played']
    team_stats['goals_conceded_per_match'] = team_stats['goals_against'] / team_stats['matches_played']
    team_stats['goal_difference_per_match'] = team_stats['goal_difference'] / team_stats['matches_played']
    team_stats['win_rate'] = (team_stats['matches_won'] / team_stats['matches_played']) * 100
    team_stats['draw_rate'] = (team_stats['matches_drawn'] / team_stats['matches_played']) * 100
    team_stats['loss_rate'] = (team_stats['matches_lost'] / team_stats['matches_played']) * 100
    team_stats['scoring_strength'] = team_stats['goals_scored_per_match'] + (0.5 * team_stats['goal_difference_per_match'])

    # Save to CSV
    os.makedirs('output', exist_ok=True)
    team_stats.to_csv('output/team_statistics.csv', index=False)

    # Generate figures
    top_teams = team_stats.sort_values(by='matches_played', ascending=False).head(15)
    fig1 = px.bar(top_teams, x='TEAM', y='scoring_strength', title='Top 15 Teams: Matches Played vs Scoring Strength', labels={'scoring_strength':'Scoring Strength'}, text='matches_played')
    fig2 = px.bar(top_teams, x='TEAM', y='goal_difference', title='Top 15 Teams: Matches Played vs Goal Difference', labels={'goal_difference':'Goal Difference'}, text='matches_played')

    # Export to HTML
    html_string = f"""
    <html>
    <head>
        <title>Team Statistics Dashboard</title>
        <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
    </head>
    <body>
        <h1>Team Statistics Dashboard</h1>
        <div id='scoring_strength' style='width:100%;height:500px;'></div>
        <div id='goal_difference' style='width:100%;height:500px;'></div>
        <script>
            var fig1 = {fig1.to_json()};
            var fig2 = {fig2.to_json()};
            Plotly.newPlot('scoring_strength', fig1.data, fig1.layout);
            Plotly.newPlot('goal_difference', fig2.data, fig2.layout);
        </script>
    </body>
    </html>
    """

    with open("output/team_dashboard.html", "w") as f:
        f.write(html_string)

if __name__ == "__main__":
    generate_dashboard()
