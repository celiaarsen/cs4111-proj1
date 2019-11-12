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

#create an array called selections to hold all desired return types
selections = []

#"conditions[]" is a list of singleConditions[]
#single condition takes strings 'compareAttr', 'compareSign', 'compareValue
#for example singleCondition[r_id, = , 5]
conditionsList = []

#Attribute lists for each entity - SYNTATICAL, words exactly as syntax of sql database
resAttribsSyn = ['r_id', 'birthplace', 'firstName', 'lastName', 'age', 'gender', 'X', 'Y', 'title']
ocuAttribsSyn = ['title', 'avg_salary', 'sei'] 
eduAttribsSyn = ['institute', 'cost', 'grad_year', 'X', 'Y']
transpoAttribsSyn = ['t_type', 'public_access', 'cost']
addressAttribsSyn = ['lot_size', 'population', 'street_number', 'city', 'X', 'Y']

#Attribute lists for each entity - COLLOQUIAL, words as users will recognize them
resAttribsCol = ['Resident ID', 'Birthplace', 'First Name', 'Last Name', 'Age',
                'Gender', 'Longitude', 'Lattitude', 'Job Title']
ocuAttribsCol = ['Job Title', 'Average Salary', 'Socio-economic Index'] 
eduAttribsCol = ['Institute', 'Cost', 'Graduation Year', 'Longitude', 'Lattitude']
transpoAttribsCol = ['Tranportation Type', 'Public Access (True/False)', 'Cost']
addressAttribsCol = ['Lot Size', 'Population', 'Street Number & Name', 'City',
                    'Longitude', 'Lattitude']


#builds SQL query based on user input
def build_sql_query():    
    query = ""
    if(len(conditionsList)==0):
        query = "SELECT * FROM %s limit 10" % ', '.join(selections)
    else:
        #print("this is conditionsList: " , conditionsList)
        #print("this is conditionsList at element 0: " , conditionsList[0])
        whereClause = "".join(conditionsList[0])
        #print("whereClause is :" , whereClause)
        query = "SELECT * FROM %s " % ', '.join(selections) + "WHERE %s limit 10" % "".join(whereClause)
        
    #print("what's in selections: ", selections)
    return query

#executes SQL query on our database!  
def execute_sql_query():
  queryResult = []
  #only execute query if user has provided input
  if(len(selections)>0):
      cursor = g.conn.execute(build_sql_query())
      for result in cursor:
          queryResult.append(result)  # can also be accessed using result[0]
      cursor.close() 
  #for debugging
  #print("whats in queryResult: ", queryResult)
  
  return queryResult
 
#takes data that have been selected and makes a list of dictionaries
def lat_lng_to_list(data):
    LAT_INDEX = 7
    LNG_INDEX = 6
    lat_long_list = []
    for row in data:
        location = {'lat':row[LAT_INDEX], 'lng': row[LNG_INDEX]}
        lat_long_list.append(location)
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
  
  queryResult = execute_sql_query()
  lat_long_data = lat_lng_to_list(queryResult)
      
  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #

  #data= names is not being used. 
  #selectionsVar is variable name in html
  #selections is variable name in server.py
  #NOTE: I CANNOT FIGURE OUT HOW TO ACCESS points IN THE JAVASCRIPT SECTION OF index.html!!!
  context = dict(data = queryResult, points = lat_long_data, selectionsVar = selections, 
                 conditionsVar = conditionsList,
                 rAS = resAttribsSyn, rAC = resAttribsCol, lenRA = len(resAttribsSyn),
                 oAS = ocuAttribsSyn, oAC = ocuAttribsCol, lenOA = len(ocuAttribsSyn),
                 eAS = eduAttribsSyn, eAC = eduAttribsCol, lenEA = len(eduAttribsSyn),
                 tAS = transpoAttribsSyn, tAC = transpoAttribsCol, lenTA = len(transpoAttribsSyn),
                 aAS = addressAttribsSyn, aAC = addressAttribsCol, lenAA = len(addressAttribsSyn))


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #

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
  


#Allows web app to route to home page through html
@app.route('/another')
def another():
  return render_template("another.html")


#Allows web app to route to home page through html
@app.route('/home')
def home():
    return render_template("home.html")

#Allows web app to route to index page through html
@app.route('/index')
def indexLink():
  return render_template("index.html")


#request.form[] is an array of all forms created in the html templates
#a dictionary was created above which allows us to parse the array with
#the name of the form as set in the html docs
#Currently, all forms are found on the index page with names:
#'name'
#"Select1'

#handles selection of return type (first field on index.html)
@app.route('/select', methods=['POST'])
def select1():
  selection = request.form['Select1']

  #checks for redundancies in return list
  redundant = False
  for i in range(0, len(selections)):
        if selection == selections[i]:
            redundant = True

  if not redundant:
    selections.append(selection) 
 
  return redirect('/')



#handles selection of condtions, second few fields, on index.html
@app.route('/conditions', methods=['POST'])
def conditions():

    singlecondition = []

    singlecondition.append(request.form['compareClass'])
    singlecondition.append(request.form['compareSign'])
    #If the attribute that we are putting the condition on is a string 
    #in the database, we need single quotes around the compare value
    if(attribute_is_str(request.form['compareClass'])):
        singlecondition.append("'"+request.form['compareValue']+"'")
    else:
        singlecondition.append(request.form['compareValue'])
            
    conditionsList.append(singlecondition) 
    
    print("this is the conditions added: ", singlecondition)

    return redirect('/')

#helper method. Checks if an attribute is a string in the Database
def attribute_is_str(attribute):
    print('the compareClass, or attricute is called ' , attribute)
    sqlQuery_getDataType = "SELECT data_type FROM information_schema.columns"
    sqlQuery_getDataType += " WHERE table_name = %s" % "".join("'"+selections[0].lower()+"'")
    sqlQuery_getDataType += " AND column_name = %s" % "".join("'"+attribute+"'")
    
    print()
    print('the sqlQuery_getDataType statement is', sqlQuery_getDataType)
    
    cursor = g.conn.execute(sqlQuery_getDataType)
    attribute_DataType = re.sub('[^A-Za-z0-9]+', '', str(cursor.next()))
    if(attribute_DataType=="character"):
        print('datatype was character')
        return True
    else:
        print('datatype was NOT CHAR')
        print('the datatype was', attribute_DataType)
        return False
    
@app.route('/grouping', methods=['POST'])
def grouping():

    #method needs to be written

    #within this method, the SQL query must be submitted to the database and the results returned

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

