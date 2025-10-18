# app/tools/fpl_query_tool.py
import psycopg2
import asyncpg
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from app.core.config import settings
from app.core.logging import logger
import os
import asyncio

# google api key
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

@tool
async def retrieve_player_team_data(user_input: str) -> dict:
    """
    Query FPL data from PostgreSQL database. Examples:
    - "Show top 10 goalscorers"
    - "Find Arsenal defenders"
    - "List fixtures for gameweek 25"
    - "Best midfielders by points"
    - "Chelsea home games"
    - "Compare Salah and Haaland"

    Args:
        user_input: Natural language query about FPL data

    Returns:
        {
            'results': List of matched data,
            'status': 'success' or 'error',
            'count': Number of results,
            'query': Generated SQL query
        }
    """
    
    try:
        logger.info(f"FPL Query: {user_input}")
        
        # Database connection using your current settings
        conn = await asyncpg.connect(settings.DB_URI_FPL)
        
        # Initialize GoogleAI LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a PostgreSQL query generator assistant. Generate SQL queries to filter FPL data from two tables:
            
            PLAYERS TABLE: "players"
            Columns: id, code, first_name, second_name, web_name, team, position, status, news, 
            chance_of_playing_next_round, chance_of_playing_this_round, now_cost, cost_change_event,
            cost_change_start, total_points, points_per_game, minutes, goals_scored, assists, 
            clean_sheets, goals_conceded, own_goals, penalties_saved, penalties_missed, yellow_cards,
            red_cards, saves, bonus, bps, influence, creativity, threat, ict_index, form, 
            dreamteam_count, selected_by_percent, transfers_in, transfers_out, transfers_in_event,
            transfers_out_event, ep_next, ep_this, starts, expected_goals, expected_assists, 
            expected_goal_involvements, expected_goals_conceded, influence_rank, creativity_rank,
            threat_rank, ict_index_rank, starts_per_90, expected_goals_per_90, expected_assists_per_90,
            expected_goal_involvements_per_90, expected_goals_conceded_per_90, clean_sheets_per_90, 
            goals_conceded_per_90, description
            
            Teams: Arsenal, Aston Villa, Bournemouth, Brentford, Brighton, Chelsea, Crystal Palace, 
            Everton, Fulham, Ipswich, Leicester, Liverpool, Man City, Man Utd, Newcastle, 
            Nott'm Forest, Southampton, Spurs, West Ham, Wolves
            
            Positions: Midfielder, Forward, Defender, Goalkeeper

            PLAYER WEB_NAMES:
            Raya, Arrizabalaga, Hein, Setford, Gabriel, Saliba, Calafiori, J.Timber, Kiwior, Lewis-Skelly, White, Clarke, Kacurri, Nichols, Saka, Ødegaard, Madueke, Martinelli, Trossard, Rice, Merino, Fábio Vieira, Nørgaard, Nwaneri, Zubimendi, Kabia, Sambi, Havertz, G.Jesus, Eze, Mosquera, Gyökeres, Dowman, Harriman-Annous, Hincapie, Martinez, M.Bizot, Gauci, Marschall, Cash, Digne, Konsa, Maatsen, Mings, Pau, A.García, Alex Moreno, Bogarde, Sousa, Yasin, Rogers, Tielemans, Bailey, Buendía, Iling Jr, Malen, McGinn, Barkley, Barrenechea, Dobbin, Kamara, Onana, Broggio, Dendoncker, Jimoh-Aloba, Young, Watkins, Redmond, Elliott, Sancho, Guessand, Wright, Rowe, Burrowes, Proctor, Patterson, Lindelöf, Weiss, Green, Hladký, Roberts, Walker, Delcroix, Dodgson, Ekdal, Estève, Hartman, Humphreys, Jordan, Lucas Pires, Sambo, Sonne, Tuanzebe, Worrall, Anthony, Benson, Bruun Larsen, Boateng, Churlinov, Cullen, Edwards, Hannibal, Koleosho, Laurent, Tchaouna, A.Ramsey, Adewumi, Banel, Trésor, Flemming, Amdouni, Foster, Barnes, Obafemi, Dúbravka, Ugochukwu, Broja, Florentino, Neto, Petrović, Dennis, McKenna, Paulsen, Zabarnyi, Senesi, Smith, Truffert, Akinmboni, Bevan, Hill, J.Araujo, Mepham, Soler, Kluivert, Semenyo, Taverner, Adams, Brooks, Christie, Cook, Philip, Scott, Sinisterra, Faivre, H.Traorè, Sadi, Silcott-Duberry, Winterburn, Evanilson, Enes Ünal, Adu-Adjei, Kroupi.Jr, Gannon-Doak, Diakité, Rees-Dottin, Adli, A.Jimenez, Milosavljeve, Nelson, O.Dango, Kelleher, Balcombe, Cox, Eyestone, Valdimarsson, Collins, Lewis-Potter, Ajer, Henry, Kayode, Pinnock, Roerslev, Van den Berg, Arthur, Fredrick, Hickey, Ji-soo, Meghoma, Schade, Damsgaard, Milambo, Carvalho, Henderson, Janelt, Jensen, Nunes, Onyeka, Yarmoliuk, Donovan, Konak, Maghoma, Peart-Harris, Trevitt, Thiago, Morgan, Steele, Verbruggen, McGill, Rushworth, Scherpen, Boscagli, Coppola, De Cuyper, Dunk, Estupiñan, F.Kadıoğlu, Lamptey, Van Hecke, Veltman, Webster, Cashin, Slater, Tasker, Mitoma, Georginio, March, Minteh, Enciso, Gruda, Hinshelwood, O'Riley, Sima, Ayari, Baleba, Gomez, Milner, Sarmiento, Watson, Wieffer, Yalcouye, Knight, Mazilu, Moran, Welbeck, Ferguson, Tzimas, Kostoulas, Buonanotte, Sánchez, Jörgensen, Penders, Slonina, Cucurella, James, Chalobah, Colwill, Gusto, B.Badiashile, Fofana, M.Sarr, Tosin, Acheampong, Anselmino, Palmer, Neto, Enzo, Estêvão, Gittens, Nkunku, Caicedo, George, Lavia, Mudryk, Andrey Santos, D.Essugo, Paez, João Pedro, Delap, N.Jackson, Marc Guiu, Garnacho, Hato, Henderson, Benitez, Matthews, Muñoz, Lacroix, Mitchell, Sosa, Guéhi, Richards, Chadi Riad, Clyne, Holding, Kporha, Sarr, Doucouré, Esse, Hughes, Kamada, Lerma, Wharton, Agbinone, Ahamada, Devenny, Ebiowei, J.Rak-Sakyi, M.França, Ozoh, Rodney, Umeh, Mateta, Nketia, Édouard, Marsh, Cardines, Yeremy, Canvot, Uche, Dewsbury-Hall, Pickford, Travers, Tyrer, Branthwaite, Tarkowski, Mykolenko, O'Brien, Coleman, Keane, Patterson, Dixon, Welch, Ndiaye, McNeil, Alcaraz, Gana, Garner, Iroegbunam, Armstrong, Bates, Ebere, Heath, Metcalfe, Barry, Beto, Y.Chermiti, Sherif, Grealish, King, Aznou, Onyango, Campbell, Dibling, Röhl, Leno, Benda, Robinson, Andersen, Bassey, Castagne, Diop, J.Cuenca, Tete, Amissah, Iwobi, Smith Rowe, Adama, Andreas, Sessegnon, Wilson, Berge, Cairney, Lukić, Godo, Harris, King, Reed, Raúl, Muniz, Lecomte, Chukwueze, Kevin, Kusi-Asare, Meslier, Cairns, Darlow, Bogle, Struijk, Bijol, Bornauw, Byram, Gudmundsson, Rodon, Schmidt, Aaronson, Gnonto, Harrison, James, Ampadu, Greenwood, Gruev, Ramazani, Tanaka, Crew, Gelhardt, Gyabi, Piroe, Bamford, Mateo Joseph, Nmecha, Longstaff, Stach, Perri, Calvert-Lewin, Okafor, Justin, Gray, A.Becker, Mamardashvili, Pécsi, Woodman, Frimpong, Kerkez, Robertson, Virgil, Konaté, Bradley, Gomez, Tsimikas, Nallo, R.Williams, Ramsay, M.Salah, Wirtz, Luis Díaz, Gakpo, Chiesa, Mac Allister, Szoboszlai, C.Jones, Gravenberch, Endo, Bajcetic, McConnell, Morton, Nyoni, Darwin, Danns, Isak, Ekitiké, Ngumoha, Leoni, Trafford, Ederson M., Ortega Moreno, Bettinelli, Aït-Nouri, Gvardiol, Akanji, Aké, Khusanov, Matheus N., Rúben, Stones, Lewis, O'Reilly, Vitor Reis, Marmoush, Foden, Savinho, Bernardo, Cherki, Doku, Gündoğan, Rodrigo, Kovačić, N.Gonzalez, Bobb, Echeverri, Reijnders, Nypan, Phillips, Haaland, Donnarumma, Mukasa, Mfuni, McAidoo, Mbeumo, Bayindir, Onana, Harrison, Heaton, Mee, De Ligt, Martinez, Mazraoui, D.Leon, Dalot, Dorgu, Maguire, Shaw, Yoro, Amass, Fredricson, Heaven, Malacia, B.Fernandes, Cunha, Rashford, Amad, Antony, Mount, Casemiro, Mainoo, Ugarte, Collyer, Fitzerald, J.Fletcher, Kone, Moorhouse, Højlund, Zirkzee, Obi, Wheatley, Šeško, Lammens, J.Ramsey, Wissa, Pope, Gillespie, Odysseas, Hall, Schär, Botman, Burn, Livramento, Trippier, Krafth, Lascelles, A.Murphy, Ashby, Pivas, Targett, Gordon, Elanga, Barnes, Bruno G., J.Murphy, Joelinton, Tonali, Antoñito C., Willock, Hayden, Kuol, L.Miley, White, Osula, Neave, Ramsdale, Thiaw, Seung soo, Woltemade, Zinchenko, McAtee, Sels, C.Miguel, Turner, Milenković, Murillo, Aina, N.Williams, David Carmo, Jair Cunha, Morato, O.Richards, Abbott, Boly, Gibbs-White, Hudson-Odoi, Anderson, Jota, Dominguez, O'Brien, Sangaré, Yates, Da Silva Moreira, Stamenic, Wood, Igor Jesus, Awoniyi, Ndoye, Gunn, Hutchinson, Kalimuendo, Douglas Luiz, John, Savona, Cuiabano, Bakwa, Patterson, Moore, Nna Noukeu, Ballard, Hume, Alese, Anderson, Cirkin, Hjelde, Huggins, Johnson, O'Nien, Pembele, Reinildo, Seelt, Adingra, Diarra, Roberts, Aleksić, E.Le Fée, Mundle, Neil, Poveda, Rigg, Sadiki, Talbi, Ba, Browne, Ekwah, H.Jones, Matete, Triantis, Isidor, Mayenda, Abdullahi, Luís Hemir, Rusyn, Xhaka, Roefs, Masuaku, Alderete, Mukiele, Geertruida, Brobbey, Traoré, Vicario, Austin, Kinsky, Pedro Porro, Romero, Danso, Davies, Dragusin, Spence, Udogie, Van de Ven, Phillips, Takai, Vuskovic, Son, Johnson, Maddison, Kudus, Kulusevski, Tel, Bentancur, Bergvall, Bissouma, Odobert, Solomon, Bryan, Gray, Moore, P.M.Sarr, Min-hyeok, Olusesi, Solanke, Richarlison, Lankshear, Scarlett, J.Palhinha, Xavi, Kolo Muani, Igor, Areola, Foderingham, Hegyi, Diouf, Emerson, Kilman, Mavropanos, N.Aguerd, Scarles, Todibo, Wan-Bissaka, Casey, L.Paquetá, Souček, Ward-Prowse, Summerville, Álvarez, Cornet, G.Rodriguez, L.Guilherme, Earthy, Irving, Orford, Potts, Bowen, Füllkrug, Marshall, Walker-Peters, Wilson, Hermansen, M.Fernandes, S.Magassa, Fabianski, Johnstone, José Sá, Bentley, Agbadou, Dohert, H.Bueno, Mosquera, R.Gomes, S.Bueno, Toti, Hoever, Meupiyou, Pedro Lima, Pond, Hee Chan, André, Bellegarde, Fer López, Gomes, Guedes, Munetsi, B.Traore, Chirewa, Edozie, Gonzalez, Hodge, Strand Larsen, Fábio Silva, Kalajdžić, Chiwome, Fraser, J.Arias, Møller Wolfe, Tchatchoua, Krejčí, Tolu
            
            FIXTURES TABLE: "fixtures"
            Columns: id, gameweek, home_team, away_team, home_difficulty, away_difficulty, 
            kickoff_time, description
            
            Difficulty levels: Very Easy, Easy, Medium, Hard, Very Hard
            Gameweeks: 1-38
            
            Rules:
            1. **Crucially, when a user asks about a player, you MUST use the `web_name` column for matching. Refer to the PLAYER WEB_NAMES list above to find the correct `web_name`.**
            2. Always include 'description' column in SELECT for rich context.
            3. Use appropriate WHERE, ORDER BY, and LIMIT clauses.
            4. For comparisons, use a single query with multiple conditions.
            5. No explanations - only the SQL query.
            
            Examples:
            - Top scorers: SELECT web_name, goals_scored, description FROM players WHERE goals_scored > 0 ORDER BY goals_scored DESC LIMIT 10
            - Team players: SELECT web_name, position, description FROM players WHERE team = 'Arsenal'
            - Fixtures: SELECT home_team, away_team, gameweek, description FROM fixtures WHERE gameweek = 25
            - Player stats for 'Saka': SELECT web_name, total_points, goals_scored, assists, description FROM players WHERE web_name = 'Saka'
            
            Query: {query}
            """
        )
        
        chain = prompt | llm
        
        # Generate SQL query
        response = await chain.ainvoke({"query": user_input})
        sql_query = response.content
        logger.info(f"Generated SQL: {sql_query}")
        
        # Clean the SQL query
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        sql_query = " ".join(line.strip() for line in sql_query.splitlines())
        
        # Execute query
        results = await conn.fetch(sql_query)
        
        # Get column names for better formatting
        if results:
            column_names = list(results[0].keys())
        else:
            column_names = []
        
        # Format results as list of dictionaries
        formatted_results = [dict(record) for record in results]
        
        await conn.close()
        
        logger.info(f"Query executed successfully. Results: {len(formatted_results)} rows")
        
        return {
            'results': formatted_results,
            'status': 'success',
            'count': len(formatted_results),
            'query': sql_query,
            'columns': column_names
        }
        
    except Exception as e:
        logger.error(f"Error in FPL query tool: {str(e)}")
        
        # Close connections if they exist
        try:
            if 'conn' in locals() and not conn.is_closed():
                await conn.close()
        except:
            pass
            
        return {
            'results': [],
            'status': 'error',
            'error': str(e),
            'count': 0
        }