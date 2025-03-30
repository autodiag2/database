#!/usr/bin/python3
from vindecoder.decoder import ISO3779_Decoder

class VIN_decoder_test:
    
    def test(self):
        #vins = [
        #    (2010,""), 
        #    (2010,""), (2010,"")
        #]
        decoder = ISO3779_Decoder(2010,"VF1BB05CF26010203")
        assert decoder.wmi["region"].lower() == "europe"
        assert decoder.wmi["country"].lower() == "france"
        assert "renault" in decoder.wmi["manufacturer"].lower()
        assert decoder.vds["engine_hint"].lower() == "gasoline"
        assert decoder.vds["plant"].lower() == "flins"
        assert decoder.vis["year"] == 2002
        assert decoder.vis["serial_number"] == "6010203"

        decoder = ISO3779_Decoder(2010,"VR7ACYHZKML019510")
        assert decoder.wmi["region"].lower() == "europe"
        assert decoder.wmi["country"].lower() == "france"
        assert "citroën" in decoder.wmi["manufacturer"].lower()
        assert "c5" in decoder.vds["family"].lower()
        assert decoder.vds["engine_type"] == "DV5RC"
        assert decoder.vis["year"] == 2021
        assert decoder.vis["serial_number"] == "019510"

        decoder = ISO3779_Decoder(2010,"VF7RD5FV8FL507366")
        assert decoder.wmi["region"].lower() == "europe"
        assert decoder.wmi["country"].lower() == "france"
        assert "citroën" in decoder.wmi["manufacturer"].lower()
        assert "c5" in decoder.vds["family"].lower()
        assert decoder.vds["engine_type"] == "EP6CDT"
        assert decoder.vis["year"] == 2015
        assert decoder.vis["serial_number"] == "507366"

        decoder = ISO3779_Decoder(2010,"JTMBF4DV4A5037027")
        assert decoder.wmi["region"].lower() == "asia"
        assert decoder.wmi["country"].lower() == "japan"
        assert "toyota" in decoder.wmi["manufacturer"].lower()
        assert decoder.vis["year"] == 2010
        assert decoder.vis["serial_number"] == "037027"

        decoder = ISO3779_Decoder(1991, "VF1B57A0410958993")
        assert decoder.wmi["region"].lower() == "europe"
        assert decoder.wmi["country"].lower() == "france"
        assert "renault" in decoder.wmi["manufacturer"].lower()
        assert decoder.vis["year"] == 1971
        assert "clio" in decoder.vds["project_code"].lower()

        decoder = ISO3779_Decoder(1991, "2T1BURHEXJC119229")
        assert decoder.wmi["region"].lower() == "north_america"
        assert decoder.wmi["country"].lower() == "canada"

        decoder = ISO3779_Decoder(2020, "4S4BSAJC9K3287952")
        assert decoder.wmi["region"].lower() == "north_america"
        assert decoder.wmi["country"].lower() == "united_states"
        assert "body_style" in decoder.vds

if __name__ == "__main__":
    VIN_decoder_test().test()