***README.txt*** 

Group
Celia Arsen -cla2143
Jack Welsh - jhw2167

*******************
To run: python3 server.py
Go to: http://35.185.0.229:8111 in a web browser

Note: the postgres database is not currently live, so data will not load if tested now (after 12/1/19)
*******************

Project Goal:

Users can filter data from the 1880 Census in New York City through a series of drop-down menus
and search boxes, and visualize the location of selected residents on an integrated Google map.

Project Description and Use:

First the user selects the attributes of the residents he/she wants returns and adds that selection to the list
	The selection will appear below to show what the user has selected

Next the user specifies any conditions they would like to place on their query:
	First they specify what category they would like to place condition on from the drop down list
	Some options include restrictions on any Resident attribute, Occupation, Address, or School (institute)
	Then they specify the kind of relationship they ate looking for by drop down ('=', '<', '!' etc)
	Then they express the value that they are search for to complete the criteria

For example
	Selections statement: Resident (by default) first name [Add Button]
	Condition statement: job title (In category Occupation) '=' Physician [Add Condition]
	Order by: First Name (optional, orders by resident ID by default)

Such a query will return the first name of all physicians in the database!

NOTE: The system will not map the results UNLESS the user selects Latitude and Longitude (or All)
from the first selection statement

NOTE 2: The database is sensitive to capitalization, to search successfully, follow the following rules of thumb
-institute and birthplace are camel case
-first name, last name, transport mode and occupation are all caps
-Longitude values (x) are decimals between -73 and -74
-Latitude values (y) are decimals between 40 and 41 
-Age, gender(1,2), public_access(0,1) are all integers

NOTE 3: A "load last query button is inserted for convenience so a user may make a query, submit it
then hit the load last query button and add additional constraints to refine the results further.










		
