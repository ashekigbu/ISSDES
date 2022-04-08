#!bin/env python3
# Author(s): cryptopal85
# Version history: April 07 2022 - Initialising main structure,
#                                - parsing capability for dbmodel and custom SQL queries
# Version history: April 08 2022 - custom input validations
#
# Remarks: Numerous data processing stages need to be repeated within different part of
# the system. Thus, instead of coding those functions each time under the relevant part of the code
# we simply use this module to make the system more portable and understandable. It does
# also allow us to easily reuse these custom functions in 'app.py and authentication.py'
# static HTML views.


import datetime, mysql.connector, uuid, string
# define and access database - https://flask.palletsprojects.com/en/2.1.x/tutorial/database/
from . import db, dbconnectalt
from . dbmodel import DataUser, User, DataGroup


##### Parse Data #####

# The following function parses grouplist strings for DataUsers, including
# converting CSV-formatted data into a list
# https://www.adamsmith.haus/python/answers/how-to-convert-a-comma-separated-string-to-a-list-in-python

def getauthsfg(glstr):
	# providing string version of object
	# removing whitespaces in digit lists
	aslist = [x.strip(' ') for x in glstr.split(',')]
	return aslist
	

##### SQL Pre-defined Statements #####


# The following function will be used to create custom SQL queries
# where supporting CRUD operations, including fetching the files end users own
# or shared across different groups. It does also meet one of the assignment requirement
# - search capability

def getauthsfilesql(uid, authgroups, ftype, fname=None, fkeytag=None):
	# selecting file meta-data from the database
	sqlselect = "select uuid_hex,filename,keywords_tags,filetype,filecreate,filesize from storedfiles where"
	agsql = "("  # authgroups
	grpcnt = len(authgroups)  # count groups
	for i in range(grpcnt):  # https://snakify.org/en/lessons/for_loop_range/
		if i < (grpcnt - 1):
			ag = "authgroups like '%{}%' or ".format(authgroups[i])
			agsql = agsql + ag
		else:
			ag = "authgroups like '%{}'".format(authgroups[i])
			agsql = agsql + ag
	agsql = agsql + " ))"
	# Search capability by filetype
	if ftype == "any":
		ftsql = "filetype is not null"
	else:
		ftsql = "filetype='{}'".format(ftype)
		
	# where clause
	sqlwhere = ftsql + "and (fileowner={} or".format(uid)
	sqlwhere = sqlwhere + agsql
	
	# additional file name or keyword arguments for where clause
	if (len(fname) > 0) and (len(fkeytag) ==0):
		sqlwhere = sqlwhere + "and (filename like '%{}%'".format(fname)
	if (len(fname) == 0) and (len(fkeytag) > 0):
		sqlwhere = sqlwhere + " and (keywords_tags like '%{}%'".format(fkeytag)
	if (len(fname) > 0) and (len(fkeytag) > 0):
		sqlwhere = sqlwhere + " and (filename like '%{}%' or keywords_tags like '%{}%')".format(fname, fkeytag)
		
	# Capability to combine different parts and get combined query
	fullsql = sqlselect + sqlwhere
	return fullsql
	

# The following function fetches binary blobs and mime types.
# It does also  validate if authenticated users are authorised to
# access particular file.
# where clauses and multiple conditions : https://www.brainbell.com/tutorials/MySQL/Combining_WHERE_Clauses.htm
def gelfiledatasql(uid, authgroups, fileuuid):
	sqlselect = "select filetype,filename,filedata, from storedfiles"
	sqlwhere = "where uuid_hex='{}' and ( fileowner={} or".format(fileuuid, uid)
	authgroups = getauthsfg(authgroups)
	agsql = "("
	grpcnt = len(authgroups)
	for i in range(grpcnt):
		if i < (grpcnt - 1):
			ag = "authgroups like '%{}%' or".format(authgroups[i])
			agsql = agsql + ag
		else:
			ag = "authgroups like '%{}%'".format(authgroups[i])
			agsql = agsql + ag
	agsql = agsql + " ))"
	sqlwhere = sqlwhere + agsql
	fullsql = sqlselect + sqlwhere
	return fullsql

	
def testfileownersql(fileuuid):
	if not isinstance(fileuuid, str):
		return None
	if len(fileuuid) != 32: # number of chars in strings
		return None
	else:
		# https://simple.wikipedia.org/wiki/Hexadecimal
		sqlselect = "select fileowner,filename from storedfiles where uuid_hex='{}'".format(fileuuid)
		return sqlselect
		

# The following function allow modification of file permissions
# only by authorised individual or a validated file owner


def updatesharedgroupssql(grouplist, fileuuid, fileowner):
	asglist = ','.join([str(x) for x in grouplist])
	updgrpsql = "update storedfiles set authgroups='{}' where uuid_hex='{}' and fileowner={}".format(asglist, fileuuid, int(fileowner))
	return updgrpsql
	
def getfiledeletesql(uid, fileuuid):
	deletesql = "delete from storedfiles where uuid_hex='{}' and fileowner='{}'".format(fileuuid, uid)
	return deletesql
	

##### SQL Queries #####

# setting up connection to SQLAlchemy
# that is needed for queries that use customised SQL statements
# https://docs.sqlalchemy.org/en/14/orm/query.html

# The following function leverages connection functions of 'init.py'
def getauthsfiles(dbconlist, appsql):
	try:
		dbhandle = dbconnectalt(dbconlist)
		thiscur = dbhandle.cursor()  # https://www.tutorialspoint.com/python_data_access/python_mysql_cursor_object.htm
		thiscur.execute(appsql)
		tuplelist = thiscur.fetchmany(size=15)  # fetch first 15 records
		dbhandle.close()
	except Exception as err:
		return None
	if isinstance(tuplelist, list):
		return tuplelist
	else:
		return None
		
def getfiledata(dbconlist, filesql):
	try:
		dbhandle = dbconnectalt(dbconlist):
		thiscur = dbhandle.cursor()
		thiscur =.execute(filesql)  # fetch file type and binary
		resulttuple = thiscur.fetchone()
		dbhandle.close()
	except Exception as err:
		return None
	if isinstance(resulttuple, tuple):
		return resulttuple  # confirm if it exists
	else:
		return None
		
def testfileownership (dbconlist, ownersql):
	try:
		dbhandle = dbconnectalt(dbconlist)
		thiscur = dbhandle.cursor()
		thiscur.execute(ownersql)
		resulttuple = thiscur.fetchone()  # fetch file type and binary
		dbhandle.close()
	except Exception as err:
		return None
	return resulttuple  # https://www.python.org/dev/peps/pep-0008/#programming-recommendations
	
def updatesharedgrp(dbconlist, shgrpsql):
	try:
		dbhandle = dbconnectalt(dbconlist)
		thiscur = dbhandle.cursor()
		resultcode = thiscur.execute(shgrpsql)
		dbhandle.commit()  # https://docs.python.org/3.10/library/sqlite3.html#sqlite3.Connection.commit
		dbhandle.close()  # https://docs.python.org/3.10/library/sqlite3.html#sqlite3.Connection.commit
	except Exception as err:
		print(err)
		return None
	return resultcode  # https://www.python.org/dev/peps/pep-0008/#programming-recommendations
	

# The following function fetch details of each group end user has authorisation
# fetching all details and moving into temporary container
def getgroupdetails(asglist):
	asgroupdetails = dict()
	for asg in asglist:
		tmplist = []
		grouprecord = DataGroup.query.filter_by(groupid=asg).first()  # http://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.first
		if grouprecord is not None:
			tmplist.append(grouprecord.groupname)
			tmplist.append(grouprecord.groupdesc)
			tmplist.append(grouprecord.grouptype)
	return asgroupdetails
	

# The following function is a database insert function to upload files
def newfileupload(dbcontlist, upsql, upval):
	try:
		dbhandle = dbconnectalt(dbcontlist)
		thiscur = dbhandle.cursor()
		result = thiscur.execute(upsql, upval)
		dbhandle.commit()
		dbhandle.close()
		return result
	except Exception as err:
		print(err)
		return None
		

# The following function is a database delete function to delete files
def deletefilerecord(dbconlist, delsql):
	try:
		dbhandle = dbconnectalt(dbconlist)
		thiscur = dbhandle.cursor()
		result = thiscur.execute(delsql)
		dbhandle.commit()
		dbhandle.close()
		return result
	except Exception as err:
		print(err)
		return None
		

