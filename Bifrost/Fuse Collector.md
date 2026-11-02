- uses nest (standard)
### Short term
- store anything canonical going in to fuse through a few events
	- all of the create *request* events -> **adds data to db**
	- release events from the snap adapter -> **removes data from db**
- exposes anything through an API
	- response formats match the canonical model
### Medium term
- polling service can look up enums per business and put them out on to the event bus
	- less frequent timer
		- do this daily
		- means new endpoint, new schedule, etc.