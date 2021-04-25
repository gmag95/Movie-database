# Movie_database

This programs allows the user to browse the complete movie database of the website IMDb, comprising more than 85000 movies and almost 300000 cast members. The back-end data was handled using postgreSQL while the interface was created with Tkinter.

The program is structured in two tabs, the first one returns a list of all the movies matching the criteria inserted by the user. The second one does the same thing for the persons. For each tab the user can also get more details about the movie/person selected clicking the button placed at the bottom of the tab.

The SQL database uses a star schema and it is composed of the following tables:
* title_principals: fact table of the database, it contains the list of all the persons credited in a movie and their role
* imdb_movies: dimension table containing detailed informations of each movie in the database
* imdb_names: dimension table containing detailed informations of each person in the database

This is an example of the detailed view of a single movie:

![Movie details](https://raw.githubusercontent.com/gmag95/Movie_database/main/example_images/Movie_example.PNG)

This is an example of the detailed view of a single person:

![Person details](https://raw.githubusercontent.com/gmag95/Movie_database/main/example_images/Person_example.PNG)

Credits to the Kaggle user <em>stefanoleone992</em> for the IMDb database.