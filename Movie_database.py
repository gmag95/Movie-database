import tkinter as tk
from tkinter import ttk
import psycopg2
import pandas as pd
from tkscrolledframe import ScrolledFrame
import re
import bs4
import requests
from PIL import ImageTk, Image
from io import BytesIO
from datetime import datetime

#support variables
        
movie_first_search=1
movie_sf=None
movie_frame=None
movie_sel_row=[]

person_first_search=1
person_sf=None
person_frame=None
person_sel_row=[]

output_image=None
movie_df=[]
person_df=[]

#function that reads the values of the entry boxes located in the movie tab
        
def movie_search_start():

    global movie_title_entry, movie_min_rat_entry, movie_max_rat_entry, movie_min_year_entry, movie_max_year_entry, movie_actor_entry, movie_role_entry
    
    parameters=["","","","","","","",""]
    
    if len(movie_title_entry.get())!=0:
        parameters[0]=movie_title_entry.get()
    
    if len(movie_min_rat_entry.get())!=0:
        try:
            parameters[1]=int(movie_min_rat_entry.get())
            if parameters[1]<0 or parameters[1]>100:
                message("minimum rating", 0)
                return
        except:
            message("mininum rating", 0)
            return

    if len(movie_max_rat_entry.get())!=0:
        try:
            parameters[2]=int(movie_max_rat_entry.get())
            if parameters[2]<0 or parameters[2]>100:
                message("maximum rating", 0)
                return
        except:
            message("maximum rating", 0)
            return

    if len(movie_genre_entry.get())!=0:
        parameters[3]=movie_genre_entry.get()
        
    if len(movie_min_year_entry.get())!=0:
        try:
            parameters[4]=int(movie_min_year_entry.get())
            if parameters[4]<1700 or parameters[4]>2025:
                message("minimum year", 0)
                return
        except:
            message("minimum year", 0)
            return

    if len(movie_max_year_entry.get())!=0:
        try:
            parameters[5]=int(movie_max_year_entry.get())
            if parameters[5]<1700 or parameters[5]>2025:
                message("maximum year", 0)
                return
        except:
            message("maximum year", 0)
            return
    
    if len(movie_actor_entry.get())!=0:
        parameters[6]=movie_actor_entry.get()
        
    if len(movie_role_entry.get())!=0:
        parameters[7]=movie_role_entry.get()

    movie_query(parameters)

#warning messages displayed when the search button is pressed

def message(field, case):
    
    pop=tk.Toplevel(root)
    pop.geometry(f"300x70+{int((ws-300)/2)}+{int((hs-70)/2)}")
    pop.grid_columnconfigure(0, weight=1)
    pop.grid_rowconfigure(0, weight=1)
    if case==0:
        pop.title("Error message")
        pop_message=tk.Label(pop, text=f"The value in the {field} field is invalid")
    else:
        pop.title("Warning")
        pop_message=tk.Label(pop, text="Showing the first 100 matches for the current query")
    pop_message.grid(sticky="nesw")
    pop_button=tk.Button(pop, text="Close this window", command=pop.destroy)
    pop_button.grid(sticky="n", pady=(0,10))

#function that highlights the selected movie or person
    
def handle_click(event, type):

    global movie_sel_row, movie_data_list, person_sel_row, person_data_list

    if type=="movie":

        if len(movie_sel_row)>0:
            for i in range(6):
                movie_data_list[movie_sel_row[0]][i].config(bg="white")
            movie_sel_row.pop()
        movie_sel_row.append(event.widget.extra)

        for i in range(6):
            movie_data_list[movie_sel_row[0]][i].config(bg="grey85")  

    else:

        if len(person_sel_row)>0:
            for i in range(4):
                person_data_list[person_sel_row[0]][i].config(bg="white")
            person_sel_row.pop()
        person_sel_row.append(event.widget.extra)

        for i in range(4):
            person_data_list[person_sel_row[0]][i].config(bg="grey85")  

#function that executes the movie query and puts the output in a pd dataframe

def movie_query(parameters):

    global movie_df, conn

    cur = conn.cursor()

    #query executed if a person name was entered

    if len(parameters[6])!=0:
        sql_select="""SELECT t.imdb_title_id, m.year, m.original_title, m.avg_vote, m.genre, n.name, t.category"""
        sql_orderby="""ORDER BY COUNT(*) OVER (PARTITION BY t.imdb_name_id) DESC, m.year DESC LIMIT 100"""

    #query executed if the person name box was left blank
    
    else:
        sql_select="""SELECT DISTINCT t.imdb_title_id, m.year, m.original_title, m.avg_vote, m.genre, m.votes"""
        sql_orderby="""ORDER BY m.votes DESC NULLS LAST LIMIT 100"""

    sql_from="""FROM title_principals t JOIN imdb_names n ON t.imdb_name_id=n.imdb_name_id JOIN imdb_movies m ON t.imdb_title_id=m.imdb_title_id"""

    params=[]

    #this part of code puts togheter the SQL conditions based on the criteria selected in the entry boxes

    blank_count=0

    if len(parameters[0])!=0:
        params.append(f"m.original_title ILIKE '%{parameters[0]}%'")
        blank_count+=1
    if len(str(parameters[1]))!=0:
        params.append(f"m.avg_vote >= {parameters[1]}")
        blank_count+=1
    if len(str(parameters[2]))!=0:
        params.append(f"m.avg_vote <= {parameters[2]}")
        blank_count+=1
    if len(parameters[3])!=0:
        params.append(f"m.genre ILIKE '{parameters[3]}%'")
        blank_count+=1
    if len(str(parameters[4]))!=0:
        params.append(f"m.year >= {parameters[4]}")
        blank_count+=1
    if len(str(parameters[5]))!=0:
        params.append(f"m.year <= {parameters[5]}")
        blank_count+=1
    if len(parameters[6])!=0:
        params.append(f"n.name ILIKE '%{parameters[6]}%'")
        blank_count+=1
    if len(parameters[7])!=0:
        params.append(f"t.category ILIKE '%{parameters[7]}%'")
        blank_count+=1

    conditions=" AND ".join(params)

    #the SQL query is put togheter and executed

    if blank_count!=0:
        sql = f"{sql_select} {sql_from} WHERE {conditions} {sql_orderby};"
    else:
        sql = f"{sql_select} {sql_from} {sql_orderby};"

    cur.execute(sql)
    movie_df = pd.DataFrame(cur.fetchall())

    movie_query_ins(movie_df)

#function that creates the on-screen grid based on the pd dataframe given as input
    
def movie_query_ins(df):

    global movie_data_list, movie_sf, movie_frame, movie_first_search, movie_sel_row
    
    #if the query returns more than 100 matches show a warnign message

    if df.shape[0]==100:

        message("", 1)

    #if a movie search was already performed destroy the previously created scrollbar

    if movie_first_search==0:
        movie_sf.destroy()
        movie_frame.destroy()
        movie_sel_row=[]

    if df.shape[0]>14:
        movie_sf = ScrolledFrame(movie_results_frame, width=700, height=320, scrollbars="vertical", relief="flat")
        movie_sf.grid(row=1)
        movie_frame = movie_sf.display_widget(tk.Canvas)

    else:
        movie_sf = ScrolledFrame(movie_results_frame, width=700, height=320, scrollbars="neither", relief="flat")
        movie_sf.grid(row=1, sticky="w", padx=(13,0))
        movie_frame=tk.Frame(movie_results_frame)
        movie_frame.grid(row=1, sticky="nw", padx=(14, 0))

    movie_data_list=[["" for y in range(6)] for x in range(df.shape[0])]

    #this part of the code populates the on-screen grid with informations

    for x in range(df.shape[0]):

        movie_data_list[x][0]=tk.Label(movie_frame, width=5, text=df.iloc[x][1], bg="white")
        movie_data_list[x][0].grid(row=x, column=0, padx=1, pady=1)
        movie_data_list[x][0].bind("<1>", lambda event: handle_click(event, "movie"))


        if len(df.iloc[x][2])>43:
            movie_data_list[x][1]=tk.Label(movie_frame, width=35, text=df.iloc[x][2][:43]+".", bg="white")  
        else:
            movie_data_list[x][1]=tk.Label(movie_frame, width=35, text=df.iloc[x][2], bg="white")

        movie_data_list[x][1].grid(row=x, column=1, padx=1, pady=1)
        movie_data_list[x][1].bind("<1>", lambda event: handle_click(event, "movie"))

        movie_data_list[x][2]=tk.Label(movie_frame, width=7, text=df.iloc[x][3], bg="white")
        movie_data_list[x][2].grid(row=x, column=2, padx=1, pady=1)
        movie_data_list[x][2].bind("<1>", lambda event: handle_click(event, "movie"))

        movie_data_list[x][3]=tk.Label(movie_frame, width=10, text=re.search(r"\w+[^,]", df.iloc[x][4])[0], bg="white")
        movie_data_list[x][3].grid(row=x, column=3, padx=1, pady=1)
        movie_data_list[x][3].bind("<1>", lambda event: handle_click(event, "movie"))

        if df.shape[1]==6:
            movie_data_list[x][4]=tk.Label(movie_frame, width=20, text="", bg="white")
            movie_data_list[x][5]=tk.Label(movie_frame, width=16, text="", bg="white")
        else:
            movie_data_list[x][4]=tk.Label(movie_frame, width=20, text=df.iloc[x][5], bg="white") 
            movie_data_list[x][5]=tk.Label(movie_frame, width=16, text=df.iloc[x][6], bg="white") 

        movie_data_list[x][4].grid(row=x, column=4, padx=1, pady=1)
        movie_data_list[x][4].bind("<1>", lambda event: handle_click(event, "movie"))
        movie_data_list[x][5].grid(row=x, column=5, padx=1, pady=1)
        movie_data_list[x][5].bind("<1>", lambda event: handle_click(event, "movie"))

        for i in range(6):
            movie_data_list[x][i].extra=(x*6+i)//6

    movie_first_search=0

#function that grabs the movie poster or the person portrait

def image_scraper(type, code):

    try:
        if type=="movie":
            site = requests.get("https://www.imdb.com/title/"+code+"/")
            soup = bs4.BeautifulSoup(site.text,"lxml")
            link=soup.find("div", class_="poster").img["src"]

        else:
            site = requests.get("https://www.imdb.com/name/"+code+"/")
            soup = bs4.BeautifulSoup(site.text,"lxml")
            link=soup.find("div", class_="image").img["src"]
            
        image = requests.get(link)

        opened_img=Image.open(BytesIO(image.content))
        resize_factor=250/opened_img.height
        opened_img=opened_img.resize((int(opened_img.width*resize_factor), 250), 3)
        my_img=ImageTk.PhotoImage(opened_img)

    #if no image was found, a blank one is created

    except:
        
        blank_img=Image.new("RGBA", (180, 250), (0,0,0,0))

        my_img=ImageTk.PhotoImage(blank_img)

    return my_img

#function that grabs from the database the movie details and put them in a pd dataframe

def movie_det_query(title):

    global conn

    cur = conn.cursor()

    sql = """
        SELECT DISTINCT m.original_title, m.year, m.avg_vote, m.votes, m.genre, m.country, m.worldwide_gross_income, m.description
        FROM title_principals t JOIN imdb_names n ON t.imdb_name_id=n.imdb_name_id JOIN imdb_movies m ON t.imdb_title_id=m.imdb_title_id 
        WHERE m.imdb_title_id = %s;
            """
    
    cur.execute(sql, [title])
    df = pd.DataFrame(cur.fetchall())
    
    return df

#function that fills the movie details pop-up window

def movie_details():

    global movie_sel_row, output_image

    if len(movie_sel_row)!=0:
        detail_df=movie_det_query(movie_df[0][movie_sel_row[0]])
        detail=tk.Toplevel(root)
        detail.geometry(f"+{int((ws-400)/2)}+{int((hs-550)/2)}")
        detail.grid_columnconfigure(0, weight=1)
        detail.grid_rowconfigure(0, weight=1)
        detail.title(movie_df[2][movie_sel_row[0]])

        output_image=image_scraper("movie", movie_df[0][movie_sel_row[0]])

        detail_title=tk.Label(detail, text=detail_df[0][0], font="verdana 20 bold", wraplength=380)
        detail_title.grid(sticky="n", row=0, pady=10, columnspan=4)
        
        detail_body_frame=tk.Frame(detail, bd=0, relief="groove", width=400, height=280)
        detail_body_frame.grid(row=1, sticky="n")
        detail_body_frame.grid_propagate(0)

        detail_image=tk.Label(detail_body_frame, image=output_image)
        detail_image.place(anchor="n", rely=0.035, relx=0.26)

        detail_year=tk.Label(detail_body_frame, text="Year:", font="verdana 8 bold", padx=10)
        detail_year.place(anchor="n", rely=0.09, relx=0.63)
        detail_rating=tk.Label(detail_body_frame, text="Rating:", font="verdana 8 bold", padx=10)
        detail_rating.place(anchor="n", rely=0.24, relx=0.63)
        detail_votes=tk.Label(detail_body_frame, text="Votes:", font="verdana 8 bold", padx=10)
        detail_votes.place(anchor="n", rely=0.39, relx=0.63)
        detail_genre=tk.Label(detail_body_frame, text="Genre:", font="verdana 8 bold", padx=10)
        detail_genre.place(anchor="n", rely=0.54, relx=0.63)
        detail_country=tk.Label(detail_body_frame, text="Country:", font="verdana 8 bold", padx=10)
        detail_country.place(anchor="n", rely=0.69, relx=0.63)
        detail_box_office=tk.Label(detail_body_frame, text="Box Office:", font="verdana 8 bold", padx=10)
        detail_box_office.place(anchor="n", rely=0.84, relx=0.63)

        detail_year_val=tk.Label(detail_body_frame, text=detail_df[1][0], padx=10)
        detail_year_val.place(anchor="n", rely=0.09, relx=0.88)
        detail_rating_val=tk.Label(detail_body_frame, text=detail_df[2][0], padx=10)
        detail_rating_val.place(anchor="n", rely=0.24, relx=0.88)
        detail_votes_val=tk.Label(detail_body_frame, text=detail_df[3][0], padx=10)
        detail_votes_val.place(anchor="n", rely=0.39, relx=0.88)
        detail_genre_val=tk.Label(detail_body_frame, text=re.search(r"\w+[^,]", detail_df[4][0])[0], padx=10)
        detail_genre_val.place(anchor="n", rely=0.54, relx=0.88)
        detail_country_val=tk.Label(detail_body_frame, text=re.search(r"\w+[^,]", detail_df[5][0])[0], padx=10)
        detail_country_val.place(anchor="n", rely=0.69, relx=0.88)

        if detail_df[6][0] != None:
            detail_box_office_val=tk.Label(detail_body_frame, text=str(round(detail_df[6][0]/1000000,2))+" M $", padx=10)
        else:
            detail_box_office_val=tk.Label(detail_body_frame, text=detail_df[6][0], padx=10)
        detail_box_office_val.place(anchor="n", rely=0.84, relx=0.88)

        detail_synopsis=tk.Label(detail, text="Synopsis", font="verdana 10 bold")
        detail_synopsis.grid(row=2, pady=5)
        detail_synopsis_val=tk.Label(detail, text=detail_df[7][0], wraplength=350)
        detail_synopsis_val.grid(row=3)
        detail_button=tk.Button(detail, text="Close this window", command=detail.destroy)
        detail_button.grid(row=4, sticky="s", pady=10, columnspan=4)

#function that reads the values of the entry boxes located in the person tab

def person_search_start():

    global person_name_entry, person_min_year_entry, person_max_year_entry, person_country_entry, deceas_var
    
    parameters=["","","","",""]
    
    if len(person_name_entry.get())!=0:
        parameters[0]=person_name_entry.get()
    
    if len(person_min_year_entry.get())!=0:
        try:
            parameters[1]=int(person_min_year_entry.get())
            if parameters[1]<1700 or parameters[1]>2025:
                message("minimum year", 0)
                return
        except:
            message("mininum year", 0)
            return

    if len(person_max_year_entry.get())!=0:
        try:
            parameters[2]=int(person_max_year_entry.get())
            if parameters[2]<1700 or parameters[2]>2025:
                message("maximum year", 0)
                return
        except:
            message("maximum year", 0)
            return

    if len(person_country_entry.get())!=0:
        parameters[3]=person_country_entry.get()
        
    if deceas_var.get()==1:
        parameters[4]=1
    else:
        parameters[4]=0
    
    person_query(parameters)

#function that executes the person query and puts the output in a pd dataframe

def person_query(parameters):

    global person_df, conn

    cur = conn.cursor()

    sql_select="SELECT DISTINCT n.imdb_name_id, n.name, n.date_of_birth, (REGEXP_MATCH(n.place_of_birth, '\w+$'))[1], COUNT(*) OVER (PARTITION BY t.imdb_name_id) AS moviescounter"
    sql_from="FROM title_principals t JOIN imdb_names n ON n.imdb_name_id=t.imdb_name_id"
    sql_orderby="ORDER BY moviescounter DESC LIMIT 100;"

    params=[]

    blank_count=0

    #this part of code puts togheter the SQL conditions based on the criteria selected in the entry boxes

    if len(parameters[0])!=0:
        params.append(f"n.name ILIKE '%{parameters[0]}%'")
        blank_count+=1
    if len(str(parameters[1]))!=0:
        params.append(f"EXTRACT(year from n.date_of_birth) >= {parameters[1]}")
    if len(str(parameters[2]))!=0:
        blank_count+=1
        params.append(f"EXTRACT(year from n.date_of_birth) <= {parameters[2]}")
    if len(parameters[3])!=0:
        blank_count+=1
        params.append(f"(REGEXP_MATCH(n.place_of_birth, '\w+$'))[1] ILIKE '{parameters[3]}%'")
    if parameters[4]==1:
        blank_count+=1
        params.append(f"n.date_of_death IS NOT NULL")

    conditions=" AND ".join(params)

    #the SQL query is put togheter and executed

    if blank_count!=0:
        sql = f"{sql_select} {sql_from} WHERE {conditions} {sql_orderby};"
    else:
        sql = f"{sql_select} {sql_from} {sql_orderby};"

    cur.execute(sql)
    person_df = pd.DataFrame(cur.fetchall())

    person_query_ins(person_df)

#function that creates the on-screen grid based on the pd dataframe given as input

def person_query_ins(df):

    global person_data_list, person_sf, person_frame, person_first_search, person_sel_row

    #if the query returns more than 100 matches show a warnign message
        
    if df.shape[0]==100:
        message("", 1)

    #if a movie search was already performed destroy the previously created scrollbar

    if person_first_search==0:
        person_sf.destroy()
        person_frame.destroy()
        person_sel_row=[]


    if df.shape[0]>15:
        person_sf = ScrolledFrame(person_results_frame, width=698, height=350, scrollbars="vertical", relief="flat")
        person_sf.grid(row=1, sticky="w", padx=(13,0))
        person_frame = person_sf.display_widget(tk.Canvas)

    else:
        person_sf = ScrolledFrame(person_results_frame, width=698, height=350, scrollbars="neither", relief="flat")
        person_sf.grid(row=1, sticky="w", padx=(13,0))
        person_frame=tk.Frame(person_results_frame)
        person_frame.grid(row=1, sticky="nw", padx=(14, 0))

    person_data_list=[["" for y in range(4)] for x in range(df.shape[0])]

    #this part of the code populates the on-screen grid with informations

    for x in range(df.shape[0]):
        person_data_list[x][0]=tk.Label(person_frame, width=40, text=df.iloc[x][1], bg="white")
        person_data_list[x][0].grid(row=x, column=0, padx=1, pady=1)
        person_data_list[x][0].bind("<1>", lambda event: handle_click(event, "person"))
        
        if df.iloc[x][2] != None:
            person_data_list[x][1]=tk.Label(person_frame, width=15, text=re.search(r"\d{4}", str(df.iloc[x][2]))[0], bg="white")  
        else:
            person_data_list[x][1]=tk.Label(person_frame, width=15, text=df.iloc[x][2], bg="white")  
        person_data_list[x][1].grid(row=x, column=1, padx=1, pady=1)
        person_data_list[x][1].bind("<1>", lambda event: handle_click(event, "person"))

        person_data_list[x][2]=tk.Label(person_frame, width=20, text=df.iloc[x][3], bg="white")
        person_data_list[x][2].grid(row=x, column=2, padx=1, pady=1)
        person_data_list[x][2].bind("<1>", lambda event: handle_click(event, "person"))

        person_data_list[x][3]=tk.Label(person_frame, width=20, text=df.iloc[x][4], bg="white")
        person_data_list[x][3].grid(row=x, column=3, padx=1, pady=1)
        person_data_list[x][3].bind("<1>", lambda event: handle_click(event, "person"))

        for i in range(4):
            person_data_list[x][i].extra=(x*4+i)//4

    person_first_search=0

#function that grabs from the database the person details and put them in a pd dataframe

def person_det_query(title):

    global conn

    cur = conn.cursor()

    #the first query grabs the personal details of the selected person

    sql = """SELECT DISTINCT n.name, n.date_of_birth, (REGEXP_MATCH(n.place_of_birth, '\w+$'))[1], 
        COUNT(*) OVER (PARTITION BY t.imdb_name_id) AS moviescounter, n.date_of_death, n.spouses, n.children, COUNT(*) OVER (PARTITION BY t.imdb_name_id)
        FROM title_principals t JOIN imdb_names n ON n.imdb_name_id=t.imdb_name_id
        WHERE n.imdb_name_id=%s;
            """

    #the second query grabs the highest and lowest rated movies of the selected person using a subquery for each movie

    sql2= """SELECT m.year, m.original_title, m.avg_vote
            FROM title_principals t JOIN imdb_names n ON n.imdb_name_id=t.imdb_name_id JOIN imdb_movies m ON t.imdb_title_id=m.imdb_title_id
            WHERE n.imdb_name_id=%s AND 
            (m.imdb_title_id=(SELECT m.imdb_title_id FROM title_principals t JOIN imdb_names n ON n.imdb_name_id=t.imdb_name_id JOIN imdb_movies m ON t.imdb_title_id=m.imdb_title_id WHERE n.imdb_name_id=%s ORDER BY m.avg_vote DESC LIMIT 1) OR m.imdb_title_id=(SELECT m.imdb_title_id FROM title_principals t JOIN imdb_names n 
            ON n.imdb_name_id=t.imdb_name_id JOIN imdb_movies m ON t.imdb_title_id=m.imdb_title_id WHERE n.imdb_name_id=%s ORDER BY m.avg_vote ASC LIMIT 1))
            ORDER BY m.avg_vote DESC;"""
    
    cur.execute(sql, [title])
    df = pd.DataFrame(cur.fetchall())
    cur.execute(sql2, [title, title, title])
    df2 = pd.DataFrame(cur.fetchall())
    return df, df2

#function that fills the person details pop-up window

def person_details():

    global person_sel_row, output_image
    
    if len(person_sel_row)!=0:
        detail_df, minmax_df=person_det_query(person_df[0][person_sel_row[0]])
        detail=tk.Toplevel(root)
        detail.geometry(f"+{int((ws-400)/2)}+{int((hs-550)/2)}")
        detail.grid_columnconfigure(0, weight=1)
        detail.grid_rowconfigure(0, weight=1)
        detail.title(person_df[1][person_sel_row[0]])
        output_image=image_scraper("person", person_df[0][person_sel_row[0]])

        per_detail_title=tk.Label(detail, text=detail_df[0][0], font="verdana 20 bold", wraplength=380)
        per_detail_title.grid(sticky="n", row=0, pady=10, columnspan=4)
        
        detail_body_frame=tk.Frame(detail, bd=0, relief="groove", width=400, height=280)
        detail_body_frame.grid(row=1, sticky="n")
        detail_body_frame.grid_propagate(0)

        per_detail_image=tk.Label(detail_body_frame, image=output_image)
        per_detail_image.place(anchor="n", rely=0.035, relx=0.26)
        
        per_detail_birth_date=tk.Label(detail_body_frame, text="Birth date:", font="verdana 8 bold", padx=10)
        per_detail_birth_date.place(anchor="n", rely=0.09, relx=0.63)
        
        
        per_detail_birth_cou=tk.Label(detail_body_frame, text="Birth country:", font="verdana 8 bold", padx=10)
        per_detail_birth_cou.place(anchor="n", rely=0.39, relx=0.63)
        per_detail_spouses=tk.Label(detail_body_frame, text="Spuses:", font="verdana 8 bold", padx=10)
        per_detail_spouses.place(anchor="n", rely=0.54, relx=0.63)
        per_detail_children=tk.Label(detail_body_frame, text="Children:", font="verdana 8 bold", padx=10)
        per_detail_children.place(anchor="n", rely=0.69, relx=0.63)
        per_detail_movies=tk.Label(detail_body_frame, text="Movies credited:", font="verdana 8 bold")
        per_detail_movies.place(anchor="n", rely=0.84, relx=0.63)

        per_detail_birth_date_val=tk.Label(detail_body_frame, text=detail_df[1][0], padx=10)
        per_detail_birth_date_val.place(anchor="n", rely=0.09, relx=0.88)

        if detail_df[1][0] is not None:
            if detail_df[4][0] is None:
                per_detail_age_val=tk.Label(detail_body_frame, text=int(((datetime.today()-datetime.strptime(str(detail_df[1][0]), "%Y-%m-%d")).days)//365.25), padx=10)
                per_detail_age=tk.Label(detail_body_frame, text="Age:", font="verdana 8 bold", padx=10)
                per_detail_age_val.place(anchor="n", rely=0.24, relx=0.88)
            else:
                per_detail_age_val=tk.Label(detail_body_frame, text=str(detail_df[4][0])+f"\n(aged {int(((detail_df[4][0]-detail_df[1][0]).days)//365.25)})", padx=10)
                per_detail_age=tk.Label(detail_body_frame, text="Death date:", font="verdana 8 bold", padx=10)
                per_detail_age_val.place(anchor="n", rely=0.21, relx=0.88)
        else:
            per_detail_age=tk.Label(detail_body_frame, text="Age:", font="verdana 8 bold", padx=10)
            per_detail_age_val=tk.Label(detail_body_frame, text=detail_df[1][0], padx=10)
        
        per_detail_age.place(anchor="n", rely=0.24, relx=0.63)

        per_detail_birth_cou_val=tk.Label(detail_body_frame, text=detail_df[2][0], padx=10)
        per_detail_birth_cou_val.place(anchor="n", rely=0.39, relx=0.88)
        per_detail_spouses_val=tk.Label(detail_body_frame, text=detail_df[5][0], padx=10)
        per_detail_spouses_val.place(anchor="n", rely=0.54, relx=0.88)
        per_detail_children_val=tk.Label(detail_body_frame, text=detail_df[6][0], padx=10)
        per_detail_children_val.place(anchor="n", rely=0.69, relx=0.88)
        per_detail_movies_val=tk.Label(detail_body_frame, text=detail_df[7][0], padx=10)
        per_detail_movies_val.place(anchor="n", rely=0.84, relx=0.88)

        best_movie_title=tk.Label(detail, text="Highest rated movie", font="verdana 10 bold")
        best_movie_title.grid(row=2, pady=5, columnspan=4)
        best_movie_title=tk.Label(detail, text="Year", font="verdana 10 bold")
        best_movie_title.grid(row=2, pady=5, padx=(35,0), sticky="w")
        best_movie_title=tk.Label(detail, text="Rating", font="verdana 10 bold")
        best_movie_title.grid(row=2, pady=5, padx=(0,35), sticky="e")
        best_movie_year=tk.Label(detail, text=minmax_df[0][0], wraplength=350)
        best_movie_year.grid(row=3, sticky="w", padx=(40,0))
        best_movie_title=tk.Label(detail, text=minmax_df[1][0], wraplength=350)
        best_movie_title.grid(row=3)
        best_movie_rating=tk.Label(detail, text=minmax_df[2][0], wraplength=350)
        best_movie_rating.grid(row=3, sticky="e", padx=(0,52))

        if minmax_df.shape[0]>1:
        
            worst_movie_title=tk.Label(detail, text="Lowest rated movie", font="verdana 10 bold")
            worst_movie_title.grid(row=4, pady=5, columnspan=4)
            best_movie_title=tk.Label(detail, text="Year", font="verdana 10 bold")
            best_movie_title.grid(row=4, pady=5, padx=(35,0), sticky="w")
            best_movie_title=tk.Label(detail, text="Rating", font="verdana 10 bold")
            best_movie_title.grid(row=4, pady=5, padx=(0,35), sticky="e")
            worst_movie_year=tk.Label(detail, text=minmax_df[0][1], wraplength=350)
            worst_movie_year.grid(row=5, sticky="w", padx=(40,0))
            worst_movie_title=tk.Label(detail, text=minmax_df[1][1], wraplength=350)
            worst_movie_title.grid(row=5)
            worst_movie_rating=tk.Label(detail, text=minmax_df[2][1], wraplength=350)
            worst_movie_rating.grid(row=5, sticky="e", padx=(0,52))


        detail_button=tk.Button(detail, text="Close this window", command=detail.destroy)
        detail_button.grid(row=6, sticky="s", pady=10, columnspan=4)

#connection to the postgres database

conn = psycopg2.connect(
    host="localhost",
    database="movie_database",
    user="postgres",
    password="imdb2021")

#the remaining part of the code creates the interface elements present in the two tabs

root=tk.Tk()
root.title("Movie database")
ws = root.winfo_screenwidth()
hs = root.winfo_screenheight()
root.geometry(f"800x600+{int((ws-800)/2)}+{int((hs-600)/2)}")

tab_parent = ttk.Notebook(root, height=560, width=775)
tab_parent.grid_propagate(0)
tab_parent.grid(padx=12, pady=(5, 12))

tab1 = ttk.Frame(tab_parent)
tab2 = ttk.Frame(tab_parent)
tab1.grid_columnconfigure(0, weight=1)
tab1.grid_rowconfigure(0, weight=1)
tab2.grid_columnconfigure(0, weight=1)
tab2.grid_rowconfigure(0, weight=1)

tab_parent.add(tab1, text="Movies")
tab_parent.add(tab2, text="Persons")

movie_search_frame=tk.Frame(tab1, bd=0, relief="groove")
movie_search_frame.grid(row=0, sticky="nw", pady=(5,0), padx=(45,0))

movie_title_label=tk.Label(movie_search_frame, text="Movie title")
movie_title_label.grid(row=0, column=0, pady=5, padx=(0,10))
movie_title_entry=tk.Entry(movie_search_frame, width=35)
movie_title_entry.grid(row=0, column=1, pady=5)

movie_rating_label=tk.Label(movie_search_frame, text="Rating (0-100)")
movie_rating_label.grid(row=0, column=2, pady=5, padx=(50, 15))

movie_min_rat_label=tk.Label(movie_search_frame, text="Min")
movie_min_rat_label.grid(row=0, column=3, pady=5)
movie_min_rat_entry=tk.Entry(movie_search_frame, width=8)
movie_min_rat_entry.grid(row=0, column=4, pady=5)

movie_max_rat_label=tk.Label(movie_search_frame, text="Max")
movie_max_rat_label.grid(row=0, column=5, pady=5)
movie_max_rat_entry=tk.Entry(movie_search_frame, width=8)
movie_max_rat_entry.grid(row=0, column=6, pady=5)

movie_genre_label=tk.Label(movie_search_frame, text="Genre")
movie_genre_label.grid(row=1, column=0, pady=5)
movie_genre_entry=tk.Entry(movie_search_frame, width=35)
movie_genre_entry.grid(row=1, column=1, pady=5)

movie_year_label=tk.Label(movie_search_frame, text="Release year")
movie_year_label.grid(row=1, column=2, padx=(50, 10), pady=5)

movie_min_year_label=tk.Label(movie_search_frame, text="Min")
movie_min_year_label.grid(row=1, column=3, pady=5)
movie_min_year_entry=tk.Entry(movie_search_frame, width=8)
movie_min_year_entry.grid(row=1, column=4, pady=5)

movie_max_year_label=tk.Label(movie_search_frame, text="Max")
movie_max_year_label.grid(row=1, column=5, pady=5)
movie_max_year_entry=tk.Entry(movie_search_frame, width=8)
movie_max_year_entry.grid(row=1, column=6, pady=5)

movie_actor_label=tk.Label(movie_search_frame, text="Person starred")
movie_actor_label.grid(row=2, column=0, pady=5, padx=(0, 10))
movie_actor_entry=tk.Entry(movie_search_frame, width=35)
movie_actor_entry.grid(row=2, column=1, pady=5)

movie_role_label=tk.Label(movie_search_frame, text="Role played")
movie_role_label.grid(row=2, column=2, pady=5, padx=(50, 10))
movie_role_entry=tk.Entry(movie_search_frame, width=35)
movie_role_entry.grid(row=2, column=3, pady=5, columnspan=4)

movies_search_button=tk.Button(tab1, text="Search movies", command=movie_search_start)
movies_search_button.grid(row=1, pady=(0,10))

movie_results_frame=tk.Frame(tab1, bd=2, relief="groove", height=405, width=750)
movie_results_frame.grid(row=2, pady=(0,10))
movie_results_frame.grid_propagate(0)
movie_results_frame.grid_columnconfigure(0, weight=1)
movie_results_frame.grid_rowconfigure(0, weight=1)

movie_data_list=[]

movie_title_frame=tk.Frame(movie_results_frame)
movie_title_frame.grid_columnconfigure(0, weight=1)
movie_title_frame.grid_rowconfigure(0, weight=1)
movie_title_frame.grid(row=0, sticky="nw", padx=(14, 0), pady=(10,0))

movie_title_list=[]

movie_title_list.append(tk.Label(movie_title_frame, width=5, text="Year", bg="grey70"))
movie_title_list[0].grid(row=0, column=0, padx=1, pady=1)
movie_title_list.append(tk.Label(movie_title_frame, width=35, text="Title", bg="grey70"))
movie_title_list[1].grid(row=0, column=1, padx=1, pady=1)
movie_title_list.append(tk.Label(movie_title_frame, width=7, text="Rating", bg="grey70"))
movie_title_list[2].grid(row=0, column=2, padx=1, pady=1)
movie_title_list.append(tk.Label(movie_title_frame, width=10, text="Genre", bg="grey70"))
movie_title_list[3].grid(row=0, column=3, padx=1, pady=1)
movie_title_list.append(tk.Label(movie_title_frame, width=20, text="Person", bg="grey70"))
movie_title_list[4].grid(row=0, column=4, padx=1, pady=1)
movie_title_list.append(tk.Label(movie_title_frame, width=16, text="Role", bg="grey70"))
movie_title_list[5].grid(row=0, column=5, padx=1, pady=1)

movie_details_button=tk.Button(movie_results_frame, text="Movie details", command=movie_details)
movie_details_button.grid(row=2, sticky="S", pady=10)

person_search_frame=tk.Frame(tab2, bd=0, relief="groove")
person_search_frame.grid(row=0, sticky="nw", pady=(5,0), padx=(35,0))

person_name_label=tk.Label(person_search_frame, text="Person name")
person_name_label.grid(row=0, column=0, pady=5, padx=(0,10))
person_name_entry=tk.Entry(person_search_frame, width=35)
person_name_entry.grid(row=0, column=1, pady=5)

person_year_label=tk.Label(person_search_frame, text="Year of birth")
person_year_label.grid(row=0, column=2, pady=5, padx=(50,30))

person_min_year_label=tk.Label(person_search_frame, text="Min")
person_min_year_label.grid(row=0, column=3, pady=5, padx=(0,6))
person_min_year_entry=tk.Entry(person_search_frame, width=8)
person_min_year_entry.grid(row=0, column=4, pady=5, padx=8)

person_max_year_label=tk.Label(person_search_frame, text="Max")
person_max_year_label.grid(row=0, column=5, pady=5, padx=6)
person_max_year_entry=tk.Entry(person_search_frame, width=8)
person_max_year_entry.grid(row=0, column=6, pady=5, padx=(8,2))

person_country_label=tk.Label(person_search_frame, text="Country of birth")
person_country_label.grid(row=1, column=0, pady=5, padx=(0,10))
person_country_entry=tk.Entry(person_search_frame, width=35)
person_country_entry.grid(row=1, column=1, pady=5)

person_deceased_label=tk.Label(person_search_frame, text="Deceased")
person_deceased_label.grid(row=1, column=2, pady=5, padx=(20,0))

deceas_var = tk.IntVar()

person_deceased_check=tk.Checkbutton(person_search_frame, variable=deceas_var)
person_deceased_check.grid(row=1, column=3, columnspan=4, pady=5)

person_search_button=tk.Button(tab2, text="Search persons", command=person_search_start)
person_search_button.grid(row=1, pady=(0,8))

person_results_frame=tk.Frame(tab2, bd=2, relief="groove", height=435, width=750)
person_results_frame.grid(row=2, pady=(0,10))
person_results_frame.grid_propagate(0)
person_results_frame.grid_columnconfigure(0, weight=1)
person_results_frame.grid_rowconfigure(0, weight=1)

person_data_list=[]

person_title_frame=tk.Frame(person_results_frame)
person_title_frame.grid_columnconfigure(0, weight=1)
person_title_frame.grid_rowconfigure(0, weight=1)
person_title_frame.grid(row=0, sticky="nw", padx=(14, 0), pady=(10,0))

person_title_list=[]

person_title_list.append(tk.Label(person_title_frame, width=40, text="Name", bg="grey70"))
person_title_list[0].grid(row=0, column=0, padx=1, pady=1)
person_title_list.append(tk.Label(person_title_frame, width=15, text="Year of birth", bg="grey70"))
person_title_list[1].grid(row=0, column=1, padx=1, pady=1)
person_title_list.append(tk.Label(person_title_frame, width=20, text="Country of birth", bg="grey70"))
person_title_list[2].grid(row=0, column=2, padx=1, pady=1)
person_title_list.append(tk.Label(person_title_frame, width=20, text="Movies credited", bg="grey70"))
person_title_list[3].grid(row=0, column=3, padx=1, pady=1)

person_details_button=tk.Button(person_results_frame, text="Person details", command=person_details)
person_details_button.grid(row=2, sticky="S", pady=10)

root.mainloop()