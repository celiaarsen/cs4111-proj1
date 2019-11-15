"""
@author: Celia Arsen and Jack Welsh
unis: cla2143 and jhw2167

Columbia's COMS W4111.001 Introduction to Databases
Based off of skeleton code by Luis Gravano

1880's NYC Census Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.

"""
import os
import flask
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import re

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@35.243.220.243/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@35.243.220.243/proj1part2"
#
DATABASEURI = "postgresql://cla2143:1868@35.243.220.243/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """

  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

   

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#


#DEFINING GLOBAL VARIABLES THAT NEED TO BE PASSED TO HTML TEMPLATE
#global querySubmitted

#warning sent to users when they attempt to do something bad
warning = ""
querySubmitted = False
limter = ""
orderBy = ""

queryResult = []
lat_long_data = []

#create an array called selections to hold all desired return types
#specificSelections stores specific attribute return types
#savedSelections allows for loading last query
selections = []
specificSelections = []
savedSelections = []
savedSpecificSelections = []

#"conditions[]" is a list of singleConditions[]
#single condition takes strings 'compareAttr', 'compareSign', 'compareValue
#for example singleCondition[r_id, = , 5]
conditionsList = []
savedConditionsList = []

entities = ['Resident', 'Address', 'Education', 'Occupation', 'Transport_Mode']

#Attribute lists for each entity - SYNTATICAL, words exactly as syntax of sql database
resAttribsSyn = ['*', 'r_id', 'birthplace', 'firstname', 'lastname', 'age', 'gender', 'X', 'Y', 'title']
ocuAttribsSyn = ['*', 'title', 'avg_salary', 'sei'] 
eduAttribsSyn = ['*', 'institute', 'X', 'Y', 'cost']
transpoAttribsSyn = ['*', 't_type', 'public_access', 'cost']
addressAttribsSyn = ['*', 'lot_size', 'population', 'street_number', 'city', 'X', 'Y']

attribsSynList = {entities[0] : resAttribsSyn, entities[1] : ocuAttribsSyn,
                 entities[2] : eduAttribsSyn, entities[3] : transpoAttribsSyn, 
                 entities[4] : addressAttribsSyn}



#Attribute lists for each entity - COLLOQUIAL, words as users will recognize them
resAttribsCol = ['All', 'Resident ID', 'Birthplace', 'First Name', 'Last Name', 'Age',
                'Gender(1,2)', 'Longitude', 'Latitude', 'Job Title']
ocuAttribsCol = ['All', 'Job Title', 'Average Salary', 'Socio-economic Index'] 
eduAttribsCol = ['All',  'Institute', 'Longitude', 'Latitude', 'Cost']
transpoAttribsCol = ['All',  'Tranportation Type', 'Public Access (True/False)', 'Cost']
addressAttribsCol = [ 'All', 'Lot Size', 'Population', 'Street Number & Name', 'City',
                    'Longitude', 'Lattitude']




#builds SQL query based on user input
def build_sql_query():

    global conditionsList
    global selections
    global specificSelections
    global orderBy
    global limiter


    #SELECTION statement
    query = "SELECT "

    selectStar = False
    if(len(selections)!=0):
        print( "this is selections: " , selections)
        for i in range(0, len(specificSelections)):
            if specificSelections[i] == "*":
                selectStar = True

        if selectStar:
            query += "*"
        else:
            for i  in range(0, len(specificSelections)):
                query += selections[i] + "." + specificSelections[i] + " "
        print("this is specific selections: ", specificSelections)    
        print("\n\n query after selection: ", query)

        #FROM statement

        query += " FROM %s" % ','.join(selections)

        print("\n\n query after From: ", query)

        #WHERE condition

    if(len(conditionsList) > 0):

        #print("this is conditionsList: " , conditionsList)
        #print("this is conditionsList at element 0: " , conditionsList[0])

        query += " WHERE "

        for i in range(0, len(conditionsList)):
             if i > 0:
                query += "AND "

             query+= "".join(conditionsList[i])
            
        print("\n\n query after WHERE: ", query)   
            
    if(orderBy!=""):

        query += " ORDER BY " + orderBy + " limit " + limiter
        
        print("\n\n query after ORDER BY: ", query)
    
    return query



#executes SQL query on our database!  
def execute_sql_query():
  queryResult = []
  #only execute query if user has provided input
  if(len(selections)>0):

      query = build_sql_query()

      print("\n\n show me the query: ", query)

      cursor = g.conn.execute(query)
      for result in cursor:
          queryResult.append(result)  # can also be accessed using result[0]
      cursor.close() 
  #for debugging
  #print("whats in queryResult: ", queryResult)
  
  return queryResult
 


#takes data that have been selected and makes a list of dictionaries
def lat_lng_to_list(data):

    global selections

    if (selections[0] == "Resident") and (specificSelections[0] == "*") :
        LAT_INDEX = 7
        LNG_INDEX = 6
        lat_long_list = []
        for row in data:
            location = {'lat':row[LAT_INDEX], 'lng': row[LNG_INDEX]}
            lat_long_list.append(location)
    elif (selections[0] == "Address") and (specificSelections[0] == "*") :
        LAT_INDEX = 5
        LNG_INDEX = 4
        lat_long_list = []
        for row in data:
            location = {'lat':row[LAT_INDEX], 'lng': row[LNG_INDEX]}
            lat_long_list.append(location)
    elif (selections[0] == "Education") and (specificSelections[0] == "*") :
        LAT_INDEX = 2
        LNG_INDEX = 1
        lat_long_list = []
        for row in data:
            location = {'lat':row[LAT_INDEX], 'lng': row[LNG_INDEX]}
            lat_long_list.append(location)
    else:
        lat_long_list = []

    return lat_long_list    



@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
  # DEBUG: this is debugging code to see what request looks like
  print(request.args)

  global querySubmitted

  global selections
  global specificSelections
  global conditionsList
  global queryResult
  global lat_long_data
  global savedConditionsList
  global savedSelections
  global savedSpecificSelections


  #Initialize vars above if statement so context always has data to select

  if querySubmitted:
    queryResult = execute_sql_query()
    lat_long_data = lat_lng_to_list(queryResult)


    #clears all lists to prepare for next query
    #but first saves them in case user wants to analyze previous results
    savedSelections = selections.copy()
    savedSpecificSelections = specificSelections.copy()
    selections = []
    specificSelections = []

    savedConditionsList = conditionsList.copy()
    conditionsList = []

    #bool must be turned back to false so queries dont run every other time
    querySubmitted = False
      
 
  #data= names is not being used. 
  #selectionsVar is variable name in html
  #selections is variable name in server.py
  context = dict(data = queryResult, points = lat_long_data, selectionsVar = selections, selVarLen = len(selections),
                 conditionsVar = conditionsList, savedSelectionsVar = savedSelections,
                 specificSelectionsVar = specificSelections, savedSpecificSelectionsVar = savedSpecificSelections,
                 rAS = resAttribsSyn, rAC = resAttribsCol, lenRA = len(resAttribsSyn),
                 oAS = ocuAttribsSyn, oAC = ocuAttribsCol, lenOA = len(ocuAttribsSyn),
                 eAS = eduAttribsSyn, eAC = eduAttribsCol, lenEA = len(eduAttribsSyn),
                 tAS = transpoAttribsSyn, tAC = transpoAttribsCol, lenTA = len(transpoAttribsSyn),
                 aAS = addressAttribsSyn, aAC = addressAttribsCol, lenAA = len(addressAttribsSyn))



  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html

  #homepage is now set to index
  #**locals()
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
  
#request.form[] is an array of all forms created in the html templates
#a dictionary was created above which allows us to parse the array with
#the name of the form as set in the html docs
#Currently, all forms are found on the index page with names:
#'name'
#"Select1'

#handles selection of return type (first field on index.html)
@app.route('/select', methods=['POST'])
def select1():

  global selections
  global specificSelections
  global attribsSynList

  selection = request.form['select1']

  specificSelection = request.form['select2']

  #checks for redundancies in return list
  redundant = False
  for i in range(0, len(selections)):
        if selection == selections[i]:
            redundant = True

  for i in range(0, len(specificSelections)):
      if specificSelection == specificSelections[i]:
        redundant = True

  compatibleAttribue = False

  #print("\n\n attrib selections list: ", attribsSynList )
  #print("\n\n and at index: ", attribsSynList[selection])

  for i in range(0,len(attribsSynList[selection])):
    if specificSelection == attribsSynList[selection][i]:
        compatibleAttribue = True
       #print("\n\n it is a compatible attribute")


  if (not redundant) and compatibleAttribue:
    selections.append(selection)
    specificSelections.append(specificSelection)
 
  return redirect('/')



#handles selection of condtions, second few fields, on index.html
@app.route('/conditions', methods=['POST'])
def conditions():

    singlecondition = []

    singlecondition.append(request.form['compareClass'])
    singlecondition.append(request.form['compareSign'])
    #If the attribute that we are putting the condition on is a string 
    #in the database, we need single quotes around the compare value
    print("the compare value: ", request.form['compareValue'])
    if(request.form['compareValue']!=""):
        if(attribute_is_str(request.form['compareClass'])):
            singlecondition.append("'"+request.form['compareValue']+"'")
        else:
            singlecondition.append(request.form['compareValue'])
            
        conditionsList.append(singlecondition) 
    
    #print("this is the conditions added: ", singlecondition)

    return redirect('/')

#helper method. Checks if an attribute is a string in the Database
def attribute_is_str(attribute): 
    
    #print('the compareClass, or attricute is called ' , attribute)
    sqlQuery_getDataType = "SELECT data_type FROM information_schema.columns"
    sqlQuery_getDataType += " WHERE table_name = %s" % "".join("'"+get_attribute_table(attribute)+"'")
    sqlQuery_getDataType += " AND column_name = %s" % "".join("'"+attribute+"'")
    
    print()
    print('the sqlQuery_getDataType statement is', sqlQuery_getDataType)
    
    cursor = g.conn.execute(sqlQuery_getDataType)
    attribute_DataType = re.sub('[^A-Za-z0-9]+', '', str(cursor.next()))
    if(attribute_DataType=="character"):
        #print('datatype was character')
        return True
    else:
        print('datatype was NOT CHAR')
        print('the datatype was', attribute_DataType)
        return False
 
#helper method
#In the conditions, we get the attribute, but not the table the attribute is from,
#and sometimes we need that information, especially if that attribute is not the table
#we want to select from
#This approach is a BANDAID and not a fix, bc there are attributes in multiple tables with
#the same names
def get_attribute_table(attribute):
    if (attribute in resAttribsSyn):
        return "resident"
    elif (attribute in ocuAttribsSyn):
        return "occupation"
    elif (attribute in eduAttribsSyn):
        return "education"
    elif (attribute in transpoAttribsSyn):
        return "transport_mode"
    else:
        return "travels_by"
        
addressAttribsSyn 

#we need to know which table the attribute we are putting the condition on is from
#call that variable attributeTable, the table from which the attribute must be pulled
@app.route('/grouping', methods=['POST'])
def grouping():

    #method needs to be written

    #within this method, the SQL query must be submitted to the database and the results returned

    return redirect('/')

@app.route('/submitQuery', methods=['POST'])
def submitQueryTrue():

    global querySubmitted
    global selections
    global orderBy
    global limiter

    if (len(selections) > 0):
        querySubmitted = True

        orderBy = request.form['orderBy']
        limiter = request.form['numberOfRecords']

    return redirect('/')


@app.route('/loadLastQuery', methods=['POST'])
def loadLastQuery():
    
    global selections
    global specificSelections
    global conditionsList
    global savedConditionsList
    global savedSelections
    global savedSpecificSelections

    if len(savedSelections) > 0:
        selections = savedSelections
        specificSelections = savedSpecificSelections

    if len(savedConditionsList) > 0:
        conditionsList = savedConditionsList

    return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()

