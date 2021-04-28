## Database Helper for SQLITE3

#### Features
* Simplified and safe shortcuts for sqlite commands.
* Avoid multiple connections to the database by agregating related commands and executing them at once.
* Don't bother about thread safety anymore.

This interface to the sqlite3 lib was built to abreviate basic sql commands through "simple" method calls
and also to queue all sql commands to run on a single database connection when possible, to avoid
multiple unnecessary database connections and become thread safe at the same time.

**Usage:**
First create a database "Main" instance with sqlite3 database file name:
* *db = db_helper.Main('myappdatabase.db')*

The module will then automatically setup itself according to the table scheme present in the file.
To check the database layout just print the database instance:
* *print(db)*

Then add basic CRUD commands to the queue by calling simple "table" methods (those are very shallow examples of usage, check detailed instructions in the proper topic):
* *db.some_table("data")* -- this will show the specified data to all entries on the table
* *db.some_table("data1", "data2" att="entry")* -- this will show "data1" and "data2" of some specific entry on the table
* *db.some_table.insert("data1", "data2", "data3", "data4")*  -- this will add a new entry to the table with the specified data
* *db.some_table.update("new_info", "entry", up_column="data")* -- this will update "entry" with "new_info" on the table

After calling the CRUD methods, use method ".run()" to execute them all together:
* *db.run()*

If you wanna check if the queued command are as you wanted before executing, just print the queue:
* *print(db.queue)*

If you want to discart the queued command before execution and empty out the queue, just call the discart method:
* *db.discart()*

Most method call will **return** a boolean to indicate wether it failed or not.
If something goes wrong when executing the command queue, you can check error messages on error_log
and also check which one was the faulty command with op_error:
* *print(db.error_log)*
* *print(db.op_error)*

Bellow you'll see detailed instructions for each pre-built sqlite command methods.

### Select

To do.

### Insert

To do.

### Update

To do.

### Delete

To do.

### Create table

To do.

### Drop table

To do.