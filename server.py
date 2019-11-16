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
resAttribsSyn = ['*', 'r_id', 'birthplace', 'firstname', 'lastname', 'age', 'gender', 'x', 'y', 'title']
ocuAttribsSyn = ['*', 'title', 'avg_salary', 'sei'] 
eduAttribsSyn = ['*', 'institute', 'cost']
transpoAttribsSyn = ['*', 't_type', 'public_access']
addressAttribsSyn = ['*', 'lot_size', 'population', 'street_number', 'city', 'X', 'Y']

attribsSynList = {entities[0] : resAttribsSyn, entities[1] : ocuAttribsSyn,
                 entities[2] : eduAttribsSyn, entities[3] : transpoAttribsSyn, 
                 entities[4] : addressAttribsSyn}



#Attribute lists for each entity - COLLOQUIAL, words as users will recognize them
resAttribsCol = ['All', 'Resident ID', 'Birthplace', 'First Name', 'Last Name', 'Age',
                'Gender(1,2)', 'Longitude', 'Latitude', 'Job Title']
ocuAttribsCol = ['All', 'Job Title', 'Average Salary', 'Socio-economic Index'] 
eduAttribsCol = ['All',  'Institute', 'Cost']
transpoAttribsCol = ['All',  'Tranportation Type', 'Public Access (True/False)']
addressAttribsCol = [ 'All', 'Lot Size', 'Population', 'Street Number & Name', 'City',
                    'Longitude', 'Latitude']



#builds SQL query based on user input
def build_sql_query():

    global conditionsList
    global selections
    global specificSelections
    global orderBy
    global limiter


    print("\n In selections, saved selections at index i | ", specificSelections, " | ", selections)


    #SELECTION statement
    query = "SELECT "

    #Value of Multitable is 1 or 2 gives 0 or 1 for multitable true or false 
    selectStar = False
    multiTable = len(set(selections)) - 1

    #print( "this is selections: " , selections)
    for i in range(0, len(specificSelections)):

       if (specificSelections[i] == "*" and selections[i] == "resident"):
           selectStar = True

    if selectStar:
        query += "*"
    elif (multiTable):

        for i  in range(0, len(specificSelections)-1):
            query += selections[0] + "." + specificSelections[i] + " "
            if(i < len(specificSelections) - 2):
                query += ", "

        if (len(conditionsList) > 0):
            query+= ", "
            for i  in range(0, len(conditionsList)):
                query += conditionsList[i][0] + conditionsList[i][1] + " "
                if(i < len(conditionsList) - 1):
                    query += ", "

    else:
        for i  in range(0, len(specificSelections)):
            query += selections[0] + "." + specificSelections[i] + " "
            if(i < len(specificSelections) - 1):
                query += ", "
                
    #print("this is specific selections: ", specificSelections)    
    #print("\n\n query after selection: ", query)

    from_where_clauses = ("", "")

    if("education" in selections):
        from_where_clauses = join_resident_education()            

    elif("occupation" in selections):
        from_where_clauses = join_resident_occupation()            

    elif("transport_mode" in selections):
        from_where_clauses = join_resident_travel()            

    elif("address" in selections):
        from_where_clauses = join_resident_address()            

    else:
        from_where_clauses = ("resident", "")

    query += " FROM %s" % from_where_clauses[0]

    #print("\n\n query after From: ", query)

    #WHERE condition
    if(multiTable):
        query += " WHERE %s" % from_where_clauses[1]
        
    if(multiTable and len(conditionsList) > 0):

        for i in range(0, len(conditionsList)):
             
             query += " AND "

             query+= "".join(conditionsList[i])
        
    if(not multiTable and len(conditionsList) > 0):      
        #print("this is conditionsList: " , conditionsList)
        #print("this is conditionsList at element 0: " , conditionsList[0])
        
        query += " WHERE "

        for i in range(0, len(conditionsList)):
             if i > 0:
                query += " AND "

             query+= "".join(conditionsList[i])
            
        print("\n\n query after WHERE: ", query)   
            
    if(orderBy!=""):

        query += " ORDER BY " + "resident." +orderBy + " limit " + limiter
        
        #print("\n\n query after ORDER BY: ", query)
    
    return query



#executes SQL query on our database!  
def execute_sql_query():
  queryResult = []
  #only execute query if user has provided input
  if(len(selections)>0):

      query = build_sql_query()

      print("\n\n show me the query: ", query)

      cursor = g.conn.execute(query)

      print("\n\n Give me the cursor cols, ", cursor.keys())

      for result in cursor:
          queryResult.append(result)  # can also be accessed using result[0]
      cursor.close() 

      queryResultTuple = (queryResult, cursor.keys())

  #for debugging
  #print("whats in queryResult: ", queryResult)
  
  return queryResultTuple
 


#takes data that have been selected and makes a list of dictionaries
def lat_lng_to_list(data):
    print()
    print()
    #print('making lat long list')

    global selections

    if (selections[0] == "resident") and (specificSelections[0] == "*") :
        LAT_INDEX = 7
        LNG_INDEX = 6
        lat_long_list = []
        for row in data:
            location = {'lat':row[LAT_INDEX], 'lng': row[LNG_INDEX]}
            lat_long_list.append(location)
    elif (selections[0] == "address") and (specificSelections[0] == "*") :
        LAT_INDEX = 5
        LNG_INDEX = 4
        lat_long_list = []
        for row in data:
            location = {'lat':row[LAT_INDEX], 'lng': row[LNG_INDEX]}
            lat_long_list.append(location)
    elif (selections[0] == "education") and (specificSelections[0] == "*") :
        LAT_INDEX = 2
        LNG_INDEX = 1
        lat_long_list = []
        for row in data:
            location = {'lat':row[LAT_INDEX], 'lng': row[LNG_INDEX]}
            lat_long_list.append(location)
    else:
        lat_long_list = []
    
    #print(lat_long_list)
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
  global warning

  global selections
  global specificSelections
  global conditionsList
  global queryResult
  global lat_long_data
  global savedConditionsList
  global savedSelections
  global savedSpecificSelections


  #Initialize vars above if statement so context always has data to select

  queryResultTuple = ("", [])

  if (querySubmitted):
    queryResultTuple = execute_sql_query()
    lat_long_data = lat_lng_to_list(queryResultTuple[0])


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
      
    #print("\n\n Show me saved selections: ", savedSelections)

  #data= names is not being used. 
  #selectionsVar is variable name in html
  #selections is variable name in server.py
  context = dict(data = queryResultTuple[0], dataHeader = queryResultTuple[1], headerLength = len(queryResultTuple[1]),
                 points = lat_long_data, selectionsVar = selections, selVarLen = len(selections),
                 conditionsVar = conditionsList, savedSelectionsVar = savedSelections, warningVar = warning,
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

  global warning

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
    selections.append(selection.lower())
    specificSelections.append(specificSelection)
    warning = ""
  else:
    warning += "Selection was redundant "

  
  print("\n In selections, in /select, saved selections at index i | ", specificSelections, " | ", selections)
 
  return redirect('/')



#handles selection of condtions, second few fields, on index.html
@app.route('/conditions', methods=['POST'])
def conditions():

    global specificSelections
    global selections
    global warning
    
    
    singlecondition = []
    addConditionBool = False
    intAttributes = ["gender", "age", "cost", "avg_salary", "sei", "public_access"]
    if(len(selections)>0 and request.form['compareValue']!=""):
        #print("the compare value: ", request.form['compareValue'])
        #print("the compare class: ", request.form['compareClass'])
        singlecondition.append(get_attribute_table(request.form['compareClass'])+'.')
        singlecondition.append(request.form['compareClass'])
        singlecondition.append(request.form['compareSign'])
        #If the attribute that we are putting the condition on is a string 
        #in the database, we need single quotes around the compare value
        
        if(request.form['compareValue']!="" and request.form['compareClass']!=""):
            if(attribute_is_str(request.form['compareClass'])):
                 sanitized_value = re.sub('[^A-Za-z0-9-.]+', '', request.form['compareValue'])              
            elif(str(request.form['compareClass']) in intAttributes):  
                sanitized_value = re.sub('[^A-Za-z0-9-.]+', '', request.form['compareValue'])
                try:
                    x = int(sanitized_value)
                except:
                    sanitized_value = -999
            else:
                try:
                    x = float(sanitized_value)
                except:
                    sanitized_value = -999
                    
            singlecondition.append("'"+str(sanitized_value)+"'")
                
            addConditionBool = True
    
        else:
           warning += "Please add a condition  |  "
    
        
    
        #print("this is the singlecondition", singlecondition)
        
        #If we are requesting an attribute that is not in the SELECT table, 
        #we should add it to selections 
        if(get_attribute_table(request.form['compareClass']) not in selections):
    
            if(len( set(selections) ) < 2):
                print("table was added to selections bc db needs to join")
                selections.append(get_attribute_table(request.form['compareClass']))
                specificSelections.append("*")
            else:
                warning += "Sorry, cant add selection because condtion value is not apart of existing selections  |  "
                addConditionBool = False;
        else:
            addConditionBool = True
    
        if addConditionBool:
             conditionsList.append(singlecondition)
             warning = ""
    else:
        warning += "Please add a selection ;)"
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
    attribute = str(attribute)

    if (attribute in resAttribsSyn):
        return "resident"
    elif (attribute in ocuAttribsSyn):
        return "occupation"
    elif (attribute in eduAttribsSyn):
        return "education"
    elif (attribute in transpoAttribsSyn):
        return "transport_mode"
    elif (attribute in addressAttribsSyn):
        return "address"
    else:
        return ""
        
def join_resident_education():
    selectFrom = "resident, attended, education"
    join_conditions = "resident.r_id=attended.r_id AND attended.institute=education.institute"
    
    join_education_info = (selectFrom, join_conditions)
    return join_education_info

def join_resident_occupation():
    selectFrom = "resident, occupation"
    join_conditions = "resident.title = occupation.title"
    
    join_occupation_info = (selectFrom, join_conditions)
    return join_occupation_info

def join_resident_travel():
    selectFrom = "resident, travels_by, transport_mode"
    join_conditions = "resident.r_id=travels_by.r_id AND travels_by.t_type=transport_mode.t_type"
    
    join_travel_info = (selectFrom, join_conditions)
    return join_travel_info

def join_resident_address():
    selectFrom = "resident, address"
    join_conditions = "resident.x=address.x AND resident.y=address.y"
    
    join_address_info = (selectFrom, join_conditions)
    return join_address_info 


@app.route('/submitQuery', methods=['POST'])
def submitQueryTrue():

    global querySubmitted
    global selections
    global orderBy
    global limiter

    global warning
    

    if (len(selections) > 0 ):
        querySubmitted = True
        warning = ""

        try:
            orderBy = request.form['orderBy']
        except:
            pass
        try:
            limiter = request.form['numberOfRecords']
        except:
            pass
    else:
        warning += "Please make a selection ;)"

    return redirect('/')


#In 94
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

