# HostsManager
A simple library to manage hosts file in python

# Scope
This library is intended to be used in a Windows or Linux environment.

# TODO
- [ ] Add a method to actually update the hosts file
- [ ] Make this library pip installable
- [ ] Finish and polish all the tests
- [ ] Whole code polishing

# What this Library does

This library has the purpose to manage dynamically a portion of the hosts file, while maintaining intact the rest of the file.  
The manager will add a Header and a Trailer where to put the hosts.  
Header and Trailer can be customized, hence, multiple istance of Manager can be used in a single hosts file with multiple and unique tuple of Header and Trailer  

# What this library doesn't perform, and never will
This library won't test if IP is reachable  
Anything related to actual networking and routing won't be performed.  
This library won't check if the IP is already outside the manager boundaries, hosts file permit multiple occurence of the same IP.  


## How to use
### With Default headers and trailers
```python
from HostsManager import HostsManager

# Init class
HM = HostsManager()
```
### With Custom Headers and Trailer
```python
from HostsManager import HostsManager

# Init class
HM = HostsManager(custom_header = "My Header", 
                  custom_trailer = "My Trailer")
```
## Debug Mode
Debug mode will use a fake hosts file to check if the output is ok with the intended purpose (playing with hosts file is never to be taken lightly)  
```python
from HostsManager import HostsManager
HM = HostsManager(debug = True)
```

## Methods
```python
# Check if there are hosts managed by the script
len(HM.hosts)

# Print the hosts in verbose mode
HM.hosts

# Print as the hosts file
print(HM.hosts)

# Add hosts
HM.addHost('172.16.10.10', ['name1', 'name2.internal'])

# Get a specific host
HM.hosts.getHostByIp('172.16.10.10')
>> 172.16.10.10 name1 name2.internal # 2023-10-14 00:47:25

# Add Name to host
myHost = HM.hosts.getHostByIp('172.16.10.10')
myHost.addName(["name3.private", "name1"])
myHost
>> 172.16.10.10 name1 name2.internal name3.private # 2023-10-14 00:47:25

# Remove a name
myHost.removeName("name1")
myHost
>> 172.16.10.10 name2.internal name3.private # 2023-10-14 00:47:25

# Remove a hosts
HM.hosts.removeHostByIp("172.16.10.10")

```