# -*- coding: utf-8 -*-

from HostsManager import HostsManager

class TestClass:
    def test_InitClass(self):
        HM = HostsManager()
        assert HM.platform == 'Windows'
        assert f"{HM.hostsPath}" == 'C:\\Windows\\System32\\drivers\\etc\\hosts'
        assert HM.header == "# START HostManager managed hosts, do not edit\n"
        assert HM.trailer in ["# END of HostManager managed hosts, do not edit\n",
                              "# END of HostManager managed hosts, do not edit"]
        assert HM.status.initiated == True
        

    def test_InitClassInDebugModeAndCustomHeaderTrailer(self):
        # test should have initiated to false cause of headers not found
        custom_header = "Test Header"
        custom_trailer = "Test Trailer"

        HM = HostsManager(debug=True, 
                        custom_header=custom_header, 
                        custom_trailer=custom_trailer)
        assert HM.platform == 'Windows'
        assert f"{HM.hostsPath}" ==  'C:\\Users\\raikoug\\AppData\\Local\\Temp\\HostsManager\\hosts'
        assert HM.header == f"# {custom_header}, do not edit\n"
        assert HM.trailer == f"# {custom_trailer}, do not edit\n"
        assert HM.status.initiated == True


    #def test_DebugClassReadHosts(self):
    #    HM = HostsManager(debug=True)
    #    assert HM.status.initiated == True
        


