import psycopg2
from settings import logger,custom_dsn

###################################################################################################
###################################################################################################

class LogTimeMain(object):

    def __init__(self,in_db_conn):
	self.id=None
	self.db_conn=in_db_conn
	self.table_name=None
	self.truncate_unit=None


    def _query_for_id(self):
	if not self.db_conn:
	    return False
	time_check_query="""SELECT CASE
    WHEN (SELECT COUNT(1) FROM {0} WHERE {1}_truncate=(SELECT date_trunc('{1}',now())::timestamp without time zone)) > 0 
    THEN NULL ELSE LOCALTIMESTAMP END AS actual_time,
    date_trunc('{1}',LOCALTIMESTAMP) AS {1}_truncate""".format(self.table_name,self.truncate_unit)
	cur=self.db_conn.cursor()
	cur.execute(time_check_query)
	time_data=cur.fetchone()
	if not time_data[0]:
	    logger.critical('Appropriate record for "{0}" already exists'.format(time_data[1]))
	    cur.close()
	    return False
#	logger.debug('Log time obtained. Actual Time: {0}\tHour Truncate: {1}'.format(time_data[0],time_data[1]))
	try:
	    cur.execute("INSERT INTO {0} ({1}_truncate,actual_time) VALUES (%s,%s) RETURNING id".format(self.table_name,self.truncate_unit),(time_data[1],time_data[0]))
	except Exception as e:
	    logger.critical("Cannot create time log record into {0}. Error: {1}".format(self.table_name,e.pgerror))
	    cur.close()
	    self.db_conn.rollback()
	    return False
	self.id=cur.fetchone()[0]
#	logger.debug("Log time ID: {0}".format(self.id))
	cur.close()
	self.db_conn.commit()
	return True


    def get_id(self):
	if not self.id:
	    if not self._query_for_id():
		return False
	return self.id
