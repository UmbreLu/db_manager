## Database Manager for SQLITE3


This plugin to the sqlite3 lib was built to abreviate basic sql commands through "simple" method calls
and also to queue all sql commands to run on a single database connection when possible, to avoid
multiple unnecessary database connections.

**Procedure:**
Table instance method call for intended sql command > operation building > operation queueing > (queue abortion or >) > operations queue execution > building fetch results > returning fetch results

**Usage example**
*db = db_manager.Main('myappdatabase.db')*
*db.sometable()* > SELECT sql command to see all table info
*db.discart()* > discart previous sql commands before executing them
*my_first_querie = db.sometable('somename')* > SELECT sql command on the table "sometable" to retrieve all info about an entry that has 'somename' info on the priority table column.
*db.run()* > execute all queue
*print(db.get(my_first_querie))*

or

*db.<table>('bla bla')*
*db.result*

**classes:**
*Main()*
*Query()*
*Table()*