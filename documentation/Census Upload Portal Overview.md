# Goal:
Build a web app that has a secure upload feature for unions to upload their census data. Web app then cleans, standardizes, stores, and distributes a "Source of Truth" census file. Allow admin members to quickly view and download files (logged) as well as control members of the website (admin functions must be for non-technical users.)
### Website structure:
- Homepage with login feature
	- Login feature only uses Microsoft and google oAuth
	- Depending on login (whether or not user is on whitelist), the user is taken to the internal access page or external access page
- Internal access
	- For Union One members on internal network only
	- Folder type organization for easy user access
		- Pulls from database
		- Downloads available as Excel files
	- Admin abilities (Ability to add, edit, or delete other admin member or union portal users)
	- All admin user actions are logged on separate table inside of database
- External access page
	- For unions wanting to upload their union census
	- Drag and drop feature to upload csv, excel, or txt
		- Module for drag and drop feature
		- Module to clean census (reformat column names and cleaning processes)
		- Module to upload to database
### Feature summary:
**[[Census Upload Portal Structure| Flask app structure]]**
- Home page leads to two separate pages (after login), each with there own functions. Session is stored until user logs out, leading back to the home page
**[[Census Upload Portal Authentication| Authentication]]**
- Microsoft and Google OAuth implemented using `msal` and `authlib`
- Role-based access using internal and external whitelists in database
- Flask-Login integration for session management
**[[Census Upload Portal Uploads and Processing| File Upload & Processing]]**
- External users can upload census files (Excel, CSV)
- Files stored as uncleaned and cleaned BLOBs in the database
- Cleaning pipeline:
    - Column mapping
    - Deduplication
    - Standardization
**[[Census Upload Portal Download and View| File Download & View]]**
- Internal users have access to a dashboard with metadata about all cleaned uploads
- Ability to download cleaned files by file ID
**[[Census Upload Portal Admin Functions | Admin Functions]]**
- List of current portal users, including union members, admin users, and SFTP users
- Ability to delete, add, and edit portal users (SFTP list is view only)
**[[Census Upload Portal Database Managing | Database Managing]]**
- Creation of unique tables holding data for separate operations via `/dataops` folder
**[[Census Upload Portal SFTP watcher | SFTP watcher]]**
- File watching functions for monitoring uploads from SFTP server
### Internal modules used:
- [[Flask Database Manager | flask-dbmanager]]
- [[Flask Drag and Drop Upload Module | flask-dragdrop]]
- [[Data Cleaning | census_cleaning]]