# -*- coding: utf-8 -*-

from platform import system
import json
from datetime import datetime
from pathlib import Path
from ipaddress import IPv4Address
from string import Template
from typing import Type
import logging
from os.path import expandvars as OSExpandVars
from os import access as OSAccess, W_OK as OSWrite, R_OK as OSRead

# logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class HostsManager:
    """
    HostsManager class
        hosts filee will have a section for hostManager managed hosts, the formar will be
            127.0.0.1 localhost
            ::1       localhost

            ...
            ...

            # START HostManager managed hosts, do not edit
            {IP_ADDRESS} {HOST_NAME} # {COMMENT with Date and Time}
            ...
            # END of HostManager managed hosts, do not edit

            ..
            ..

    """
    ## Class Private variables
    __supported_platforms       = ['Linux', 'Windows']
    __defualt_header            = "# START HostManager managed hosts, do not edit\n"
    __defualt_trailer           = "# END of HostManager managed hosts, do not edit\n"
    __custom_header_template    = Template("# $header, do not edit\n")
    __custom_trailer_template   = Template("# $trailer, do not edit\n")
    __linux_hosts_path          = '/etc/hosts'
    __windows_hosts_path        = 'C:\\Windows\\System32\\drivers\\etc\\hosts'
    __immutable_variables       = ['hostsPath', 'header', 'trailer', 'status', 'platform']

    ## Class Public variables
    hostsPath: Path
    header: str
    trailer: str
    platform: str


    def __init__(self, debug: bool = False, 
                 custom_header: str = None, 
                 custom_trailer: str = None):
        """
        HostsManager constructor
            Parameters:
                custom_header: str - custom header to be used instead of the defualt one, will fill the Template:
                    "# $header, do not edit"
                custom_trailer: str - custom trailer to be used instead of the defualt one, will fill the Template:
                    "# $trailer, do not edit"
                debug: bool - if True, will use a fake hosts file, under /tmp/HostsManager/hosts on Linux
                                or %TEMP%/HostsManager/hosts on Windows

        """
        # Verify what platform the script is running in
        self.platform = system()

        # If platform is different from linux or windows, raise an error
        if self.platform not in HostsManager.__supported_platforms:
            raise HostsManager.InvalidPlatform(f"Unsupported platform: {self.platform}")

        # define the hosts file path based on the platform
        self.hostsPath = Path(self.__getHostsPath())

        # If debug flag, use a fake hosts file.
        # On Linux under /tmp folder, file HostsManager_hosts
        # On windows under %TEMP%/HostsManager folder, hosts file
        if debug:
            logging.debug("Debug mode enabled, using fake hosts file.")
            if self.platform == 'Linux':
                logging.debug("Platform is Linux, using /tmp/HostsManager/hosts")
                self.hostsPath = Path('/tmp/HostsManager/hosts')
            elif self.platform == 'Windows':
                logging.debug("Platform is Windows, using %TEMP%/HostsManager/hosts")
                self.hostsPath = Path( OSExpandVars("%TEMP%")) / 'HostsManager/hosts'
            
            # Create the folder and file if they don't exist
            logging.debug("Creating folder if it doesn't exist")
            self.hostsPath.parent.mkdir(parents=True, exist_ok=True)
            logging.debug("Creating file if it doesn't exist")  
            self.hostsPath.touch()
        
        # check read/write rights on self.hostsPath
        self.__checkReadWriteRights(self.hostsPath)
            
        
        # Define defualt headers and trailers
        if custom_header:
            self.header = HostsManager.__custom_header_template.substitute(header=custom_header)
        else:
            self.header = HostsManager.__defualt_header
        if custom_trailer:
            self.trailer = HostsManager.__custom_trailer_template.substitute(trailer=custom_trailer)
        else:
            self.trailer = HostsManager.__defualt_trailer

        
        
        # Check if the headers and trailers are in the hosts file
        self.status = HostsManager.Status(self.__checkHeadersAndTrailers())

        if not self.status.initiated:
            # If the headers and trailers are not in the hosts file, initialize the hosts file
            self.status.initiated = self.__initHostsManager()
        
        # If the headers and trailers are in the hosts file, read the file and store the data in a class
        self.__getManagedHosts()


    # Public HostsManager methods
    def addHost(self, ip: str, name: list[str]):
        # check if ip is an actual IPv4 address
        
        ip = IPv4Address(ip)

        tmpHost: HostsManager.Host = self.hosts.getHostByIp(ip)
        if tmpHost:
            tmpHost.addName(name)
        else:
            self.hosts.addHost(ip, name)

    

        

    # Private HostsManager methods
    def __getHostsPath(self) -> str:
        """
        Returns the hosts file path based on the platform
        """
        if self.platform == 'Linux':
            return HostsManager.__linux_hosts_path
        elif self.platform == 'Windows':
            return HostsManager.__windows_hosts_path
    
    def __checkHeadersAndTrailers(self) -> bool:
        """
        Checks if the headers and trailers are in the hosts file.
            Cases are:
                - Both headers and trailers are in the file: return True
                - Both headers and trailers are not in the file: return False
                - Only one of the headers or trailers is in the file: raise an error
        """
        # check if the file has the headers and trailers
        with self.hostsPath.open('r') as f:
            lines = f.readlines()
        
        headerLine: bool = False
        trailerLine: bool = False

        if self.header in lines:
            # header found
            headerLine = True
        
        # check traiver with \n at the end
        if self.trailer in lines:
            # trailer found
            trailerLine = True
        
        # check trailer without \n at the end
        if self.trailer[:-1] in lines:
            # trailer found
            trailerLine = True
        
        # if both true return true
        if headerLine and trailerLine:
            return True

        # if both false return false
        if (not headerLine) and (not trailerLine):
            return False

        # otherwise avoid any modification of hosts due to corruption
        if not headerLine:
            raise HostsManager.HeaderMissing(f"Header missing from hosts file: {self.hostsPath}, trailer is present. Cannot procede.")
        if not trailerLine:
            raise HostsManager.TrailerMissing(f"Trailer missing from hosts file: {self.hostsPath}, header is present. Cannot procede.")
        
        raise HostsManager.UnkownError(f"Unkown error occured while checking headers and trailers in hosts file: Reached End of Function without result.")

    def __checkReadWriteRights(self, path: Path):
        """
        Checks if the user has read/write rights on the file.
        """
        _ = path.open('r').readlines()
        _ = path.open('a').write('')

    def __getManagedHosts(self):
        """
        Reads the hosts file and stores the data in a class
        """
        with self.hostsPath.open('r') as f:
            lines = f.readlines()
        
        # remove the header and trailer from the list
        lines = lines[lines.index(self.header)+1:lines.index(self.trailer)]

        # parse the list and create a list of Host objects
        self.hosts = HostsManager.Hosts()
        for line in lines:
            self.hosts.append(HostsManager.Host.getHostFromHostString(line))
            
    def __initHostsManager(self) -> bool:
        """
        Initializes the hosts file adding headers and trailer at the end of the file
        """
        # add header and trailer to the file
        with self.hostsPath.open('a') as f:
            f.write(self.header)
            f.write(self.trailer)
        
        # set the status to initiated
        return self.__checkHeadersAndTrailers()

    # HostsManager Classes
    class Status:
        initiated: bool

        def __init__(self, status: bool):
            self.initiated = status

    class Hosts(list):
        """
        Hosts class
            Methods
                getHostByIp(ip: IPv4Address) -> Host|None
                    Returns a list of Host objects or None
        """

        def getHostByIp(self, ip: IPv4Address):
            """
            return host with ip or None
            """
            if isinstance(ip, str):
                try:
                    ip = IPv4Address(ip)
                except:
                    return None

            for host in self:
                if host.ip == ip:
                    return host
            return None
        
        def getHostByName(self, name: str) -> list:
            """
            return a list host with name or []
            """
            result = list()
            for host in self:
                if name in host.name:
                    result.append(host)
            return result

        def addHost(self, ip: IPv4Address, name: list[str], comment: datetime = datetime.now()):
            """
            Appends a Host object to the list
            """
            self.append(HostsManager.Host(ip, name, comment))

        def removeHostByIp(self, ip: IPv4Address):
            """
            Removes a Host object from the list by ip
            """
            self.remove(self.getHostByIp(ip))
        
        def __str__(self) -> str:
            result = ""
            for host in self:
                result += str(host) + "\n"
            return result

        def __repr__(self) -> str:
            return self.__str__()

    class Host:
        """
        Host class
            Methods
                getHostFromHostString(host_string: str) -> Host
                    Returns a Host object from a host string
        """
        ip: IPv4Address
        name: list[str]
        comment: datetime

        def __init__(self, ip: IPv4Address, name: list[str], comment: datetime = datetime.now()):
            self.ip = ip
            self.name = name
            self.comment = comment
        
        def getHostFromHostString(host_string: str):
            """
            Returns a Host object from a host string
                Host string should be 
                    {IP_ADDRESS} [{HOST_NAME}] # {COMMENT with Date and Time in timestamp format}
            """
            # Ip is the first field
            ip = host_string.split()[0]

            # names are the others untile and # is found
            string_without_comment = host_string.split('#')[0]
            names = string_without_comment.split()[1:]

            # comment is the last field
            comment = host_string.split('#')[1].strip()

            #type conversions
            ip = IPv4Address(ip)
            # comment has to be converted from timestamp to datetime
            date = datetime.fromtimestamp(float(comment))

            return HostsManager.Host(ip, names, date)

        def addName(self, name: list[str]):
            # merge to have unique names
            new_names = list(set(self.name + name))
            if list(set(self.name)) != new_names:
                self.name = new_names
                self.updateComment()

        def removeName(self, name: str):
            if len(self.name) == 1:
                raise ValueError("Cannot remove the last name from a host.")
            self.name.remove(name)
        
        def updateComment(self):
            """
            Updates the comment with the current timestamp
            """
            self.comment = datetime.now()
            
        def __str__(self) -> str:
            # comment has to be converted to timestamp
            return f"{self.ip} {' '.join(self.name)} # {self.comment.timestamp()}"
        
        def __repr__(self) -> str:
            # represent comment as date with format %Y-%m-%d %H:%M:%S
            return f"{self.ip} {' '.join(self.name)} # {self.comment.strftime('%Y-%m-%d %H:%M:%S')}"

    ### # Dunder methods for immutability
    ### def __setattr__(self, name, value):
    ###     if name in HostsManager.__immutable_variables:
    ###         raise AttributeError("Cannot modify .thingies")
    ###     else:
    ###         return type.__setattr__(self, name, value)
    ### 
    ### def __delattr__(self, name):
    ###     if name in HostsManager.__immutable_variables:
    ###         raise AttributeError("Cannot delete .thingies")
    ###     else:
    ###         return type.__delattr__(self, name)

    # HostsManager error classes
    class InvalidPlatform(Exception):
        """
        Raised when the platform is not supported.
        """
        pass

    class HeaderMissing(Exception):
        """
        Raised when the header is missing from the hosts file, but the trailer is there.
        """
        pass

    class TrailerMissing(Exception):
        """
        Raised when the trailer is missing from the hosts file, but the header is there.
        """
        pass

    class UnkownError(Exception):
        """
        Raised when an unkown error occurs.
        """
        pass

